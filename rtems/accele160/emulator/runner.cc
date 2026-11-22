#include "third_party/sim5/include/Core.h"
#include "board_memory.h"
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>
#include <cerrno>
#include <cctype>
#include <cstdio>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <algorithm>
#include <unordered_map>
#include <array>
#include <utility>

static uint32_t word(const std::vector<char>& image, size_t offset) {
    return static_cast<uint8_t>(image.at(offset)) |
           static_cast<uint32_t>(static_cast<uint8_t>(image.at(offset + 1))) << 8 |
           static_cast<uint32_t>(static_cast<uint8_t>(image.at(offset + 2))) << 16 |
           static_cast<uint32_t>(static_cast<uint8_t>(image.at(offset + 3))) << 24;
}

// Instruction count shared by the direct loop and bridge-driven stepping,
// used only to timestamp PCI register trace lines.
static uint64_t g_trace_cycle = 0;

static void printAudit() {
    const auto audit = getBoardMemoryAudit();
    std::cout << std::hex << std::setfill('0');
    if (const auto retry = exploratoryConfigRetryState(); retry.modeled)
        std::cout << "checkpoint config-retry-summary released="
                  << (retry.released ? 1 : 0) << " ebcr=" << std::setw(4)
                  << retry.ebcr << " release-cycle=" << std::dec
                  << retry.release_cycle << std::hex << " release-ip="
                  << std::setw(8) << retry.release_ip << " pci-reg-writes="
                  << std::dec << retry.register_writes << std::hex << "\n";
    if (audit.unknown_write)
        std::cout << "audit first-unmodeled-write=" << std::setw(8)
                  << audit.first_write << "\n";
    if (audit.unknown_read)
        std::cout << "audit first-unmodeled-read=" << std::setw(8)
                  << audit.first_read << "\n";
}

static void printNativeReport(Core& core) {
    std::cout << std::hex << std::setfill('0') << "checkpoint native-report";
    for (unsigned i = 0; i < 16; ++i)
        std::cout << " " << std::setw(8) << core.read32(0xc0001f00 + 4 * i);
    std::cout << "\n";
    std::cout << "checkpoint thread executing=" << std::setw(8)
              << core.read32(0xc001c040) << " heir=" << std::setw(8)
              << core.read32(0xc001c050) << " idle=" << std::setw(8)
              << core.read32(0xc001c1b0) << "\n";
}

static void dumpAperture(Core& core, const std::string& path) {
    if (path.empty()) return;
    std::ofstream output(path, std::ios::binary);
    if (!output) throw std::runtime_error("cannot open aperture output");
    for (uint32_t address = 0xc0000000; address < 0xc0002000; address += 4) {
        const uint32_t value = core.read32(address);
        for (unsigned shift = 0; shift < 32; shift += 8)
            output.put(static_cast<char>(value >> shift));
    }
    if (!output) throw std::runtime_error("cannot write aperture output");
    std::cout << "checkpoint aperture-dump path=" << path
              << " base=c0000000 bytes=8192\n";
}

static bool deliverExploratoryTimer0(Core& core) {
    constexpr uint32_t tint0 = 1u << 12;
    if (!(core.read32(0xff008500) & tint0) ||
        !(core.read32(0xff008504) & tint0) ||
        (core.read32(0xff008510) & (1u << 10)) ||
        !core.interruptsEnabled()) return false;
    const uint8_t vector = static_cast<uint8_t>(
        (((core.read32(0xff008528) >> 16) & 15u) << 4) | 2u);
    if (vector < 8 || vector / 8 <= core.currentPriority()) return false;
    core.write32(0xff008500, core.read32(0xff008500) & ~tint0);
    core.deliverExternalInterrupt(vector);
    return true;
}

static void traceStockInterruptSetup(Core& core) {
    const Address ip = core.currentIP();
    if (ip != 0xc0051af0 && ip != 0xc0051b7c &&
        ip != 0xc0051dc0 && ip != 0xc0054f2c &&
        ip != 0xc0054f68 && ip != 0xc0054f78) return;
    std::cout << std::hex << std::setfill('0')
              << "checkpoint stock-interrupt-setup ip=" << std::setw(8) << ip
              << " g4=" << std::setw(8) << core.readGPR(20)
              << " g5=" << std::setw(8) << core.readGPR(21)
              << " g6=" << std::setw(8) << core.readGPR(22)
              << " g7=" << std::setw(8) << core.readGPR(23)
              << " r7=" << std::setw(8) << core.readGPR(7)
              << " channels=" << std::setw(8) << core.read32(0xc00c0150)
              << " pirsr-before=" << std::setw(8) << core.read32(0x1050)
              << "\n" << std::flush;
}

static std::pair<uint32_t, uint32_t> boardContextKind(Core& core) {
    const uint32_t context = core.read32(0xc04ad650);
    if (context < 0xc0000000u || context > 0xc0ffffe8u)
        return {context, 0};
    return {context, core.read32(context + 0x14)};
}

// Bridge-only 80303 interrupt-router probe. The caller supplies an asserted
// peripheral source; IMAP, IMSK, CPU priority, and the stock pin routing
// decide whether the corresponding handler may run.
static uint8_t routeExploratoryInterruptPin(Core& core, unsigned pin) {
    if (pin > 3 && pin != 7) return 0;
    const bool asserted = pin < 4
        ? ((core.read16(0x8bf0000c) & 1u) &&
           (core.read16(0x8bf0000a) & 4u) &&
           (core.read32(0xc0384b68) & (1u << pin)))
        : (inboundMuUnmaskedStatus() & 4u);
    if (!asserted) return 0;
    const uint32_t bit = 1u << pin;
    if (pin < 4 && !(core.read32(0x1050) & bit)) return 0;
    core.write32(0xff008500, core.read32(0xff008500) | bit);
    if (!(core.read32(0xff008504) & bit) || !core.interruptsEnabled()) return 0;
    const uint32_t imap = core.read32(pin < 4 ? 0xff008520 : 0xff008524);
    const unsigned nibble = (imap >> (4u * (pin & 3u))) & 15u;
    if (!nibble) return 0;
    const uint8_t vector = static_cast<uint8_t>((nibble << 4) | 2u);
    if (vector / 8 <= core.currentPriority()) return 0;
    core.deliverExternalInterrupt(vector);
    return vector;
}

// Local test-only link: one request per line, one eight-digit hex response.
// R/W expose controller RAM in the first 16 MiB. M latches the inbound MU
// event; S advances the CPU after a host event; I/C inspect/modify local MU
// registers for tests. H stages the two host PCI command registers in local
// MMIO for an exploratory readiness test. No host DMA read or interrupt entry
// is implied.
static void serveBridge(Core& core, const std::string& path,
                        bool exploratory_timer_clock,
                        bool exploratory_timer_interrupt,
                        bool exploratory_isp_no_device_auto,
                        bool trace_scan_state3,
                        bool trace_priority,
                        bool model_s3_flash) {
    if (path.empty()) return;
    if (path.size() >= sizeof(sockaddr_un::sun_path))
        throw std::runtime_error("bridge socket path too long");
    int listener = socket(AF_UNIX, SOCK_STREAM, 0);
    if (listener < 0) throw std::runtime_error("bridge socket creation failed");
    sockaddr_un address{};
    address.sun_family = AF_UNIX;
    std::strncpy(address.sun_path, path.c_str(), sizeof(address.sun_path) - 1);
    unlink(path.c_str());
    if (bind(listener, reinterpret_cast<sockaddr*>(&address), sizeof(address)) ||
        listen(listener, 1)) {
        close(listener);
        throw std::runtime_error("bridge socket bind/listen failed");
    }
    std::cout << "checkpoint bridge-ready path=" << path << "\n" << std::flush;
    std::cout << std::hex << std::setfill('0')
              << "checkpoint cpu-interrupt-state prcb=" << std::setw(8)
              << core.currentPRCB() << " table=" << std::setw(8)
              << core.currentInterruptTable() << " priority=" << std::dec
              << static_cast<unsigned>(core.currentPriority())
              << " enabled=" << core.interruptsEnabled() << "\n" << std::flush;
    bool saw_timer_interrupt = false;
    unsigned post_interrupt_trace = 0;
    unsigned stock_isr_returns = 0;
    unsigned calibrated_delay_prints = 0;
    bool saw_qlogic_mailbox_poll = false;
    bool saw_isp_load_command = false;
    bool saw_mu_request_helper = false;
    bool saw_mu_message_read = false;
    bool saw_mu_request_return = false;
    bool saw_mu_queue_handoff = false;
    bool saw_mu_request_callback = false;
    bool saw_mu_outbound_publish = false;
    bool saw_mu_dma_wait = false;
    unsigned scan_state3_traces = 0;
    unsigned scan_status_write_traces = 0;
    unsigned scan_worker_traces = 0;
    unsigned priority_trace_count = 0;
    unsigned low_priority_trace_count = 0;
    std::unordered_map<Address, uint32_t> scan_worker_states;
    // QEMU owns the first connection; tests may reconnect after it exits to
    // inspect registers and step the CPU without resetting the controller.
    for (;;) {
    int connection = accept(listener, nullptr, nullptr);
    if (connection < 0) { unlink(path.c_str()); close(listener); throw std::runtime_error("bridge accept failed"); }
    FILE *stream = fdopen(connection, "r+");
    if (!stream) { close(connection); unlink(path.c_str()); close(listener); throw std::runtime_error("bridge fdopen failed"); }
    char line[256];
    while (fgets(line, sizeof(line), stream)) {
        char op = 0;
        unsigned addr = 0, size = 0, value = 0;
        if (line[0] == 'B') {
            /* Offline-only bounded DRAM upload. One bridge request writes
             * exactly 64 bytes; the host must still step the i960 CPU. */
            char hex[129]{};
            bool valid = std::sscanf(line, "B %x %128s", &addr, hex) == 2 &&
                         std::strlen(hex) == 128 &&
                         (addr & 63u) == 0u &&
                         addr >= 0xc0000000u && addr <= 0xc0ffffc0u;
            for (unsigned i = 0; valid && i < 128; ++i)
                valid = std::isxdigit(static_cast<unsigned char>(hex[i]));
            if (!valid) {
                std::fputs("ERR\n", stream);
            } else {
                for (unsigned i = 0; i < 16; ++i) {
                    unsigned byte[4];
                    for (unsigned j = 0; j < 4; ++j)
                        std::sscanf(hex + i * 8 + j * 2, "%2x", &byte[j]);
                    core.write32(addr + i * 4,
                        byte[0] | (byte[1] << 8) | (byte[2] << 16) |
                        (byte[3] << 24));
                }
                std::fputs("00000000\n", stream);
            }
        } else if (line[0] == 'M' || line[0] == 'N') {
            const bool ring_slot = line[0] == 'N';
            unsigned long long dma = 0;
            char hex[129]{};
            bool valid = std::sscanf(line, "%*c %llx %128s", &dma, hex) == 2 &&
                         std::strlen(hex) == 128;
            for (unsigned i = 0; valid && i < 128; ++i)
                valid = std::isxdigit(static_cast<unsigned char>(hex[i]));
            std::array<uint8_t, 64> mailbox_bytes{};
            for (unsigned i = 0; valid && i < mailbox_bytes.size(); ++i) {
                unsigned byte = 0;
                valid = std::sscanf(hex + i * 2, "%2x", &byte) == 1;
                mailbox_bytes[i] = static_cast<uint8_t>(byte);
            }
            if (!valid || !(ring_slot ? stageExploratoryHostRingSlot(
                                      dma, mailbox_bytes.data(), mailbox_bytes.size()) :
                                  submitInboundMailboxPayload(
                                      dma, mailbox_bytes.data(), mailbox_bytes.size()))) {
                std::fputs("ERR\n", stream);
            } else if (ring_slot) {
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint memory-mailbox-slot dma=" << std::setw(16)
                          << dma << " bytes=" << hex << " staged=1 completion=unmodeled\n"
                          << std::flush;
                std::fputs("00000000\n", stream);
            } else {
                unsigned id = 0, opcode = 0, ioctl = 0;
                std::sscanf(hex, "%2x", &id);
                unsigned high = 0;
                std::sscanf(hex + 2, "%2x", &high);
                id |= high << 8;
                std::sscanf(hex + 4, "%2x", &opcode);
                std::sscanf(hex + 42, "%2x", &ioctl);
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint mailbox-submission dma=" << std::setw(16)
                          << dma << " id=" << std::setw(4) << id
                          << " opcode=" << std::setw(2) << opcode
                          << " ioctl=" << std::setw(2) << ioctl
                          << " completion=unmodeled\n" << std::flush;
                std::cout << "checkpoint mailbox-bytes " << hex << "\n" << std::flush;
                std::fputs("00000000\n", stream);
            }
        } else if (line[0] == 'G') {
            char kind = 0;
            unsigned long long dma = 0;
            unsigned length = 0;
            if (std::sscanf(line, "G %c %llx %u", &kind, &dma, &length) == 3 &&
                registerExploratoryHostGuestWindow(kind, dma, length)) {
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint host-guest-window kind=" << kind
                          << " dma=" << std::setw(16) << dma
                          << " bytes=" << std::dec << length << "\n" << std::flush;
                std::fputs("00000000\n", stream);
            } else {
                std::fputs("ERR\n", stream);
            }
        } else if (line[0] == 'S' && std::sscanf(line, "S %u", &size) == 1 &&
                   size <= 1000000) {
            if (exploratory_isp_no_device_auto) {
                const uint32_t responses =
                    postExploratoryIspNoDeviceScanResponses();
                const uint8_t vector = routeExploratoryInterruptPin(core, 0);
                if (responses || vector)
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint isp-no-device-auto responses="
                              << std::dec << responses << std::hex
                              << " vector=" << std::setw(2)
                              << static_cast<unsigned>(vector)
                              << " pirsr=" << std::setw(8)
                              << core.read32(0x1050) << "\n" << std::flush;
            }
            const uint64_t timer_events_before = exploratoryTimer0Events();
            const uint32_t isp_completions_before = exploratoryIspMailboxCompletions();
            unsigned timer_interrupts = 0;
            unsigned gate_loops = 0, gate_exits = 0, unmask_hits = 0;
            unsigned command_dispatch = 0, mu_setup = 0, mu_poll = 0;
            unsigned mu_dispatch = 0, mu_receive = 0;
            unsigned mmbox_bit4 = 0, mmbox_ring_scan = 0;
            unsigned console_return = 0, boot_marker = 0, next_wait = 0, next_stage = 0;
            unsigned init_entry = 0, board_callback = 0, mu_init = 0;
            unsigned startup_monitor_init = 0, startup_monitor_tick = 0;
            unsigned isp_service = 0, isp_response_worker = 0;
            unsigned isp_status_entry = 0;
            unsigned scan_init = 0, scan_tick = 0;
            unsigned controller_scan_tick = 0, scan_worker_schedule = 0;
            unsigned qlogic_discovery = 0, qlogic_setup = 0, qlogic_delay = 0;
            unsigned qlogic_delay_calls = 0;
            unsigned isp_status_calls = 0;
            uint32_t init_progress = 0;
            uint32_t monitor_progress = 0;
            constexpr Address init_checkpoints[] = {
                0xc004d710, 0xc004d720, 0xc004d728, 0xc004d730,
                0xc004d740, 0xc004d778, 0xc004d790, 0xc004d794,
                0xc004d798, 0xc004d7a0,
            };
            unsigned post_gate_trace = 0;
            Address interrupt_history[64]{};
            unsigned interrupt_history_count = 0;
            std::unordered_map<Address, unsigned> samples;
            std::unordered_map<Address, unsigned> delay_callers;
            Address previous_step_ip = 0;
            for (unsigned i = 0; i < size && core.lastFault() == NoFault; ++i) {
                if (core.currentIP() == 0xc001c5fc && stock_isr_returns++ < 8)
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint stock-isr-ret pfp=" << std::setw(8)
                              << core.readGPR(0) << " rip=" << std::setw(8)
                              << core.readGPR(2) << " fp=" << std::setw(8)
                              << core.readGPR(31) << " sp=" << std::setw(8)
                              << core.readGPR(1) << " depth=" << std::dec
                              << core.callDepth() << " priority="
                              << static_cast<unsigned>(core.currentPriority())
                              << "\n" << std::flush;
                if (timer_interrupts)
                    interrupt_history[interrupt_history_count++ & 63u] = core.currentIP();
                if (post_interrupt_trace) {
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint interrupt-trace ip=" << std::setw(8)
                              << core.currentIP() << " insn=" << std::setw(8)
                              << core.read32(core.currentIP()) << " fp="
                              << std::setw(8) << core.readGPR(31) << " rip="
                              << std::setw(8) << core.readGPR(2) << "\n" << std::flush;
                    --post_interrupt_trace;
                }
                if (core.currentIP() == 0xc00534a0)
                    ++delay_callers[previous_step_ip];
                if (core.currentIP() == 0xc0052e1c) ++gate_loops;
                if (core.currentIP() == 0xc0052e3c) {
                    ++gate_exits;
                    post_gate_trace = 32;
                }
                if (post_gate_trace) {
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint post-gate ip=" << std::setw(8)
                              << core.currentIP() << "\n" << std::flush;
                    --post_gate_trace;
                }
                if (core.currentIP() == 0xc004d7fc) ++unmask_hits;
                if (core.currentIP() == 0xc004d640) ++init_entry;
                if (core.currentIP() == 0xc004d700) {
                    ++board_callback;
                    if (board_callback == 1) {
                        const Address object = core.read32(0xc04ad650);
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint board-callback object=" << std::setw(8)
                                  << object << " target=" << std::setw(8)
                                  << core.read32(object + 0x174) << "\n" << std::flush;
                    }
                }
                if (core.currentIP() == 0xc004d7a0) ++mu_init;
                if (core.currentIP() == 0xc009fb60) ++startup_monitor_init;
                if (core.currentIP() == 0xc006ef80) ++isp_service;
                if (core.currentIP() == 0xc006f8f0) ++isp_response_worker;
                if (core.currentIP() == 0xc006fd40) ++isp_status_entry;
                if (core.currentIP() == 0xc002f680) ++scan_init;
                if (core.currentIP() == 0xc002f840) ++scan_tick;
                if (trace_scan_state3 && core.currentIP() == 0xc002fb1c &&
                    scan_state3_traces++ < 24) {
                    const Address object = core.readGPR(6);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint scan-state3 object=" << std::setw(8)
                              << object << " state=" << std::setw(8)
                              << core.read32(object + 0x14) << " field28="
                              << std::setw(8) << core.read32(object + 0x28)
                              << " channel-status=" << std::setw(8)
                              << core.read32(0xc0384bb8) << " channel-flag="
                              << std::setw(8) << core.read32(0xc0384bbc)
                              << " slot=" << std::setw(8)
                              << core.read32(0xc00c3690) << "\n" << std::flush;
                }
                if (trace_scan_state3 &&
                    (core.currentIP() == 0xc002fa8c ||
                     core.currentIP() == 0xc002fc00) &&
                    scan_status_write_traces++ < 24) {
                    const Address object = core.currentIP() == 0xc002fa8c ?
                                           core.readGPR(5) : core.readGPR(9);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint scan-field28-write ip=" << std::setw(8)
                              << core.currentIP() << " object=" << std::setw(8)
                              << object << " old=" << std::setw(8)
                              << core.read32(object + 0x28) << "\n" << std::flush;
                }
                if (trace_scan_state3 && core.currentIP() == 0xc002fb14) {
                    const Address object = core.readGPR(6);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint scan-owner-state3-set object="
                              << std::setw(8) << object << " field28="
                              << std::setw(8) << core.read32(object + 0x28)
                              << " channel-flag=" << std::setw(8)
                              << core.read32(0xc0384bbc) << "\n" << std::flush;
                }
                if (trace_scan_state3 && core.currentIP() == 0xc002ffc8) {
                    const Address device = core.readGPR(4);
                    const uint32_t state = core.read32(device + 0xb0);
                    auto [it, inserted] = scan_worker_states.emplace(device, state);
                    if (inserted || it->second != state) {
                        it->second = state;
                        if (scan_worker_traces++ < 40)
                            std::cout << std::hex << std::setfill('0')
                                      << "checkpoint scan-worker-state device="
                                      << std::setw(8) << device << " state="
                                      << std::setw(8) << state << " result="
                                      << std::setw(8) << core.read32(device + 0x0c)
                                      << " attempts=" << std::setw(8)
                                      << core.read32(device + 0xa4)
                                      << " field40=" << std::setw(8)
                                      << core.read32(device + 0x40)
                                      << "\n" << std::flush;
                    }
                }
                if (core.currentIP() == 0xc002ff90) ++controller_scan_tick;
                if (core.currentIP() == 0xc00516b0) ++qlogic_discovery;
                traceStockInterruptSetup(core);
                if (core.currentIP() == 0xc006e890) ++qlogic_setup;
                if (core.currentIP() == 0xc00505f0) ++qlogic_delay;
                if (core.currentIP() == 0xc00534a0) {
                    ++qlogic_delay_calls;
                    if (calibrated_delay_prints++ < 8)
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint calibrated-delay caller="
                                  << std::setw(8) << previous_step_ip
                                  << " units=" << std::setw(8)
                                  << core.readGPR(16) << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc006bddc && !saw_qlogic_mailbox_poll) {
                    saw_qlogic_mailbox_poll = true;
                    const Address chip = core.readGPR(5);
                    const auto chip16 = [&](Address offset) {
                        const Address address = chip + offset;
                        return (core.read32(address & ~Address{3}) >>
                                ((address & 2u) * 8u)) & 0xffffu;
                    };
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint qlogic-mailbox-poll chip=" << std::setw(8)
                              << chip << " hccr=" << std::setw(4)
                              << chip16(0xc0) << " isr=" << std::setw(4)
                              << chip16(0x0a) << " semaphore="
                              << std::setw(4) << chip16(0x0c)
                              << " mailbox0=" << std::setw(4)
                              << chip16(0x70) << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc006bc30 && !saw_isp_load_command) {
                    const Address args = core.readGPR(17);
                    if (args >= 0xc0000000u && args <= 0xc0fffff0u &&
                        core.read16(args) == 9) {
                        saw_isp_load_command = true;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint isp-load-call caller=" << std::setw(8)
                                  << previous_step_ip << " args=" << std::setw(8)
                                  << args << " mb1=" << std::setw(4)
                                  << core.read16(args + 2) << " mb2=" << std::setw(4)
                                  << core.read16(args + 4) << " mb3=" << std::setw(4)
                                  << core.read16(args + 6) << " mb4=" << std::setw(4)
                                  << core.read16(args + 8) << "\n" << std::flush;
                    }
                }
                if (core.currentIP() == 0xc006bc30 && isp_status_calls < 4) {
                    const Address args = core.readGPR(17);
                    if (args >= 0xc0000000u && args <= 0xc0fffff0u &&
                        core.read16(args) == 0x001fu) {
                        ++isp_status_calls;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint isp-status-call caller="
                                  << std::setw(8) << previous_step_ip
                                  << " args=" << std::setw(8) << args
                                  << " output=" << std::setw(8)
                                  << core.readGPR(18) << " input-count="
                                  << std::setw(8) << core.readGPR(19)
                                  << " output-count=" << std::setw(8)
                                  << core.readGPR(20) << "\n" << std::flush;
                    }
                }
                if (core.currentIP() == 0xc002fb00) {
                    ++scan_worker_schedule;
                    if (scan_worker_schedule <= 3)
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint scan-worker-schedule id="
                                  << std::setw(8) << core.readGPR(16)
                                  << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc002f868 && scan_tick <= 3) {
                    const Address scan = core.readGPR(6);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint scan-state object=" << std::setw(8)
                              << scan << " state=" << std::setw(8)
                              << core.read32(scan + 0x14) << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc009fcc0) {
                    ++startup_monitor_tick;
                    if (startup_monitor_tick <= 3)
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint startup-monitor-tick index="
                                  << std::setw(8) << core.read32(0xc00c3690)
                                  << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc009fce8 && startup_monitor_tick <= 3) {
                    const Address state = core.readGPR(4);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint startup-monitor-state object="
                              << std::setw(8) << state << " state="
                              << std::setw(8) << core.read32(state + 4)
                              << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc009fd84)
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint startup-allocation result="
                              << std::setw(8) << core.readGPR(16)
                              << "\n" << std::flush;
                if (core.currentIP() == 0xc009fd94)
                    std::cout << "checkpoint startup-allocation success\n" << std::flush;
                constexpr Address monitor_checkpoints[] = {
                    0xc009fd98, 0xc009fdc0, 0xc009fdc4,
                    0xc009fdc8, 0xc009fe48,
                };
                for (unsigned j = 0; j < sizeof(monitor_checkpoints) / sizeof(monitor_checkpoints[0]); ++j) {
                    if (core.currentIP() == monitor_checkpoints[j] && !(monitor_progress & (1u << j))) {
                        monitor_progress |= 1u << j;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint monitor-progress ip=" << std::setw(8)
                                  << core.currentIP() << "\n" << std::flush;
                    }
                }
                for (unsigned j = 0; j < sizeof(init_checkpoints) / sizeof(init_checkpoints[0]); ++j) {
                    if (core.currentIP() == init_checkpoints[j] && !(init_progress & (1u << j))) {
                        init_progress |= 1u << j;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint init-progress ip=" << std::setw(8)
                                  << core.currentIP() << "\n" << std::flush;
                    }
                }
                if (core.currentIP() == 0xc009ff7c) {
                    ++command_dispatch;
                    if (command_dispatch == 1)
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint command-dispatch r4=" << std::setw(8)
                                  << core.readGPR(4) << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc004d7a0) ++mu_setup;
                if (core.currentIP() == 0xc004e6b8 && !saw_mu_message_read) {
                    saw_mu_message_read = true;
                    std::array<uint8_t, 16> host_bytes{};
                    const uint32_t base = exploratoryHostDmaBase();
                    const bool backed = readExploratoryHostDma(
                        base, host_bytes.data(), host_bytes.size());
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-message-read message0=" << std::setw(8)
                              << core.read32(0x1310) << " message1=" << std::setw(8)
                              << core.read32(0x1314) << " staged-base=" << std::setw(8)
                              << base << " staged=" << backed << " prefix=";
                    if (backed)
                        for (const auto byte : host_bytes)
                            std::cout << std::setw(2) << static_cast<unsigned>(byte);
                    std::cout << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc004e740 && !saw_mu_request_helper) {
                    saw_mu_request_helper = true;
                    const Address descriptor = core.readGPR(5);
                    std::array<uint8_t, 16> host_bytes{};
                    const bool backed = readExploratoryHostDma(
                        core.read32(0x1310), host_bytes.data(), host_bytes.size());
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-request-helper descriptor=" << std::setw(8)
                              << descriptor << " g1=" << std::setw(8)
                              << core.readGPR(17) << " host-bus=" << std::setw(8)
                              << core.read32(0x1310) << " host-backed=" << backed;
                    if (descriptor >= 0xc0000000u && descriptor <= 0xc0ffffe0u)
                        for (unsigned offset = 0; offset < 32; offset += 4)
                            std::cout << " d" << offset << '=' << std::setw(8)
                                      << core.read32(descriptor + offset);
                    std::cout << " host-prefix=";
                    if (backed)
                        for (const auto byte : host_bytes)
                            std::cout << std::setw(2) << static_cast<unsigned>(byte);
                    std::cout << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc004e744 && !saw_mu_request_return) {
                    saw_mu_request_return = true;
                    const Address descriptor = core.readGPR(5);
                    const Address result = core.readGPR(16);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-request-return descriptor=" << std::setw(8)
                              << descriptor << " result=" << std::setw(8)
                              << result << " dma1254=" << std::setw(8)
                              << core.read32(0x1254) << " dma1260=" << std::setw(8)
                              << core.read32(0x1260) << " dma1264=" << std::setw(8)
                              << core.read32(0x1264);
                    if (descriptor >= 0xc0000000u && descriptor <= 0xc0ffffe0u)
                        for (unsigned offset = 0; offset < 32; offset += 4)
                            std::cout << " d" << offset << '=' << std::setw(8)
                                      << core.read32(descriptor + offset);
                    if (result >= 0xc0000000u && result <= 0xc0ffffc0u)
                        for (unsigned offset = 0; offset < 64; offset += 4)
                            std::cout << " r" << offset << '=' << std::setw(8)
                                      << core.read32(result + offset);
                    std::cout << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc004e790 && !saw_mu_queue_handoff) {
                    saw_mu_queue_handoff = true;
                    const Address request_object = core.readGPR(5);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-queue-handoff object=" << std::setw(8)
                              << request_object << " companion=" << std::setw(8)
                              << core.readGPR(6);
                    if (request_object >= 0xc0000000u && request_object <= 0xc0ffff60u)
                        for (unsigned offset : {0u, 4u, 0x10u, 0x50u, 0x84u, 0x98u})
                            std::cout << " o" << offset << '=' << std::setw(8)
                                      << core.read32(request_object + offset);
                    std::cout << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc004fcf0 && !saw_mu_request_callback) {
                    saw_mu_request_callback = true;
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-request-callback object=" << std::setw(8)
                              << core.readGPR(16) << " queue-head=" << std::setw(8)
                              << core.read32(0xc0385290) << " dma1254=" << std::setw(8)
                              << core.read32(0x1254) << " dma1260=" << std::setw(8)
                              << core.read32(0x1260) << " dma1264=" << std::setw(8)
                              << core.read32(0x1264) << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc004e808 && !saw_mu_outbound_publish) {
                    saw_mu_outbound_publish = true;
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-outbound-publish omr0=" << std::setw(8)
                              << core.read32(0x1318) << " omr1=" << std::setw(8)
                              << core.read32(0x131c) << " odb=" << std::setw(8)
                              << core.read32(0x132c) << " request=" << std::setw(8)
                              << core.read32(0xc0385290) << "\n" << std::flush;
                }
                if (saw_mu_message_read && core.currentIP() == 0xc004f6c0 &&
                    !saw_mu_dma_wait) {
                    saw_mu_dma_wait = true;
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint mu-dma0-wait status=" << std::setw(8)
                              << core.read32(0x1404) << " callback=" << std::setw(8)
                              << core.read32(0xc00c37c8) << "\n" << std::flush;
                }
                if (core.currentIP() == 0xc00535a4) ++mu_poll;
                if (core.currentIP() == 0xc004e870) ++mu_dispatch;
                if (core.currentIP() == 0xc004e660) ++mu_receive;
                if (core.currentIP() == 0xc004e900) ++mmbox_bit4;
                if (core.currentIP() == 0xc004fa50 ||
                    core.currentIP() == 0xc004fb20) ++mmbox_ring_scan;
                if (core.currentIP() == 0xc0052e48) ++console_return;
                if (core.currentIP() == 0xc0052e60) ++boot_marker;
                if (core.currentIP() == 0xc0052e9c) {
                    const Address object = core.read32(0xc04ad650);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint board-mode flags=" << std::setw(2)
                              << (core.read32(object + 0x70) & 0xffu)
                              << " object=" << std::setw(8) << object << "\n"
                              << std::flush;
                }
                if (core.currentIP() == 0xc0052e80) ++next_wait;
                if (core.currentIP() == 0xc0052f18) ++next_stage;
                if ((i & 63u) == 0) ++samples[core.currentIP()];
                previous_step_ip = core.currentIP();
                const auto priority_before = trace_priority ? core.currentPriority() : 0;
                noteExploratoryTraceCycle(++g_trace_cycle, core.currentIP());
                core.cycle();
                const auto priority_after = trace_priority ? core.currentPriority() : 0;
                if (trace_priority && priority_before != priority_after &&
                    (priority_trace_count++ < 96 ||
                     (priority_after < 8 && low_priority_trace_count < 16)))
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint priority-change ip=" << std::setw(8)
                              << previous_step_ip << " next=" << std::setw(8)
                              << core.currentIP() << std::dec << " before="
                              << static_cast<unsigned>(priority_before) << " after="
                              << static_cast<unsigned>(priority_after)
                              << " depth=" << core.callDepth() << "\n" << std::flush;
                if (trace_priority && priority_before != priority_after &&
                    priority_after < 8) ++low_priority_trace_count;
                if (core.lastFault() != NoFault) {
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint fault-origin ip=" << std::setw(8)
                              << previous_step_ip << " insn=" << std::setw(8)
                              << core.read32(previous_step_ip) << " next="
                              << std::setw(8) << core.currentIP() << " code="
                              << std::setw(8) << core.lastFault() << "\n" << std::flush;
                    if (timer_interrupts) {
                        std::cout << "checkpoint interrupt-tail";
                        const unsigned count = std::min(interrupt_history_count, 64u);
                        for (unsigned j = 0; j < count; ++j)
                            std::cout << ' ' << std::hex << std::setw(8)
                                      << interrupt_history[(interrupt_history_count - count + j) & 63u];
                        std::cout << "\n" << std::flush;
                    }
                }
                if (exploratory_timer_clock) advanceExploratoryBusClock();
                if (exploratory_timer_interrupt && core.lastFault() == NoFault &&
                    deliverExploratoryTimer0(core)) {
                    if (!saw_timer_interrupt) post_interrupt_trace = 32;
                    saw_timer_interrupt = true;
                    ++timer_interrupts;
                }
            }
            std::cout << std::hex << std::setfill('0')
                      << "checkpoint bridge-step count=" << std::dec << size
                      << " ip=" << std::hex << std::setw(8) << core.currentIP()
                      << " fault=" << std::setw(8) << core.lastFault()
                      << std::dec << " gate-loops=" << gate_loops
                      << " gate-exits=" << gate_exits
                      << " unmask=" << unmask_hits
                      << " command-dispatch=" << command_dispatch
                      << " mu-setup=" << mu_setup
                      << " mu-poll=" << mu_poll
                      << " mu-dispatch=" << mu_dispatch
                      << " mu-receive=" << mu_receive
                      << " mmbox-bit4=" << mmbox_bit4
                      << " mmbox-ring-scan=" << mmbox_ring_scan
                      << " console-return=" << console_return
                      << " boot-marker=" << boot_marker
                      << " next-wait=" << next_wait
                          << " next-stage=" << next_stage
                          << " init-entry=" << init_entry
                          << " board-callback=" << board_callback
                          << " mu-init=" << mu_init
                          << " startup-monitor-init=" << startup_monitor_init
                          << " startup-monitor-tick=" << startup_monitor_tick
                          << " isp-service=" << isp_service
                          << " isp-response-worker=" << isp_response_worker
                          << " isp-status-entry=" << isp_status_entry
                          << " scan-init=" << scan_init
                          << " scan-tick=" << scan_tick
                          << " controller-scan-tick=" << controller_scan_tick
                          << " scan-worker-schedule=" << scan_worker_schedule
                          << " qlogic-discovery=" << qlogic_discovery
                          << " qlogic-setup=" << qlogic_setup
                          << " qlogic-delay=" << qlogic_delay
                          << " qlogic-delay-calls=" << qlogic_delay_calls
                      << " isp-mailbox-completions=" <<
                             (exploratoryIspMailboxCompletions() - isp_completions_before)
                      << " timer0-events=" <<
                             (exploratoryTimer0Events() - timer_events_before)
                      << " timer0-interrupts=" << timer_interrupts
                      << " priority-changes=" << priority_trace_count
                      << " below8-transitions=" << low_priority_trace_count
                      << "\n"
                      << std::flush;
            std::vector<std::pair<Address, unsigned>> frequent(samples.begin(), samples.end());
            std::sort(frequent.begin(), frequent.end(), [](const auto& a, const auto& b) {
                return a.second > b.second;
            });
            for (size_t i = 0; i < std::min<size_t>(frequent.size(), 6); ++i)
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint bridge-sample ip=" << std::setw(8)
                          << frequent[i].first << std::dec << " count="
                          << frequent[i].second << "\n" << std::flush;
            for (const auto& caller : delay_callers)
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint delay-caller ip=" << std::setw(8)
                          << caller.first << std::dec << " count="
                          << caller.second << "\n" << std::flush;
            std::fprintf(stream, "%08x\n", core.currentIP());
        } else if (line[0] == 'E' &&
                   std::sscanf(line, "E %x", &value) == 1 &&
                   (value <= 3 || value == 7)) {
            if (value == 7) enableExploratoryMuDmaTrace();
            const uint8_t vector = routeExploratoryInterruptPin(core, value);
            std::cout << std::hex << std::setfill('0')
                      << "checkpoint routed-interrupt pin=" << value
                      << " vector=" << std::setw(2)
                      << static_cast<unsigned>(vector)
                      << " ip=" << std::setw(8) << core.currentIP()
                      << " ipnd=" << std::setw(8) << core.read32(0xff008500)
                      << " imsk=" << std::setw(8) << core.read32(0xff008504)
                      << " imap0=" << std::setw(8) << core.read32(0xff008520)
                      << " imap1=" << std::setw(8) << core.read32(0xff008524)
                      << " pirsr=" << std::setw(8) << core.read32(0x1050)
                      << " isp-isr=" << std::setw(4) << core.read16(0x8bf0000c)
                      << " isp-sem=" << std::setw(4) << core.read16(0x8bf0000a)
                      << " priority=" << std::dec
                      << static_cast<unsigned>(core.currentPriority())
                      << "\n" << std::flush;
            std::fprintf(stream, "%08x\n", vector ? core.currentIP() : 0u);
        } else if (line[0] == 'N' &&
                   (line[1] == '\n' || line[1] == '\0')) {
            // Explicit bridge probe; NativeCore validates the submitted IOCBs.
            std::fprintf(stream, "%08x\n",
                         postExploratoryIspNoDeviceScanResponses());
        } else if (line[0] == 'J' &&
                   std::sscanf(line, "J %x", &value) == 1 &&
                   (value == 0x42 || value == 0x62 || value == 0x72) &&
                   core.interruptsEnabled() &&
                   (value == 0x42 || value == 0x62 ||
                    value / 8 > core.currentPriority())) {
            // Diagnostic vector source injection bypasses the unmodeled
            // 80303 external interrupt router. Honor the CPU priority gate
            // whenever the mapped vector is eligible.
            if (value == 0x62) enableExploratoryMuDmaTrace();
            const bool forced_priority = value / 8 <= core.currentPriority();
            if (forced_priority)
                core.forceExternalInterruptForProbe(static_cast<uint8_t>(value));
            else
                core.deliverExternalInterrupt(static_cast<uint8_t>(value));
            post_interrupt_trace = 48;
            std::cout << std::hex << std::setfill('0')
                      << "checkpoint exploratory-isp-vector vector="
                      << std::setw(2) << value << " ip=" << std::setw(8)
                      << core.currentIP() << " entry-word=" << std::setw(8)
                      << core.read32(core.currentIP()) << " ipnd=" << std::setw(8)
                      << core.read32(0xff008500) << " imsk=" << std::setw(8)
                      << core.read32(0xff008504) << " channel-mask=" << std::setw(8)
                      << core.read32(0xc0384b68)
                      << " forced-priority=" << forced_priority
                      << "\n" << std::flush;
            std::fprintf(stream, "%08x\n", core.currentIP());
        } else if (line[0] == 'D' &&
                   std::sscanf(line, "D %x", &value) == 1) {
            postExploratoryInboundDoorbell(value);
            std::cout << std::hex << std::setfill('0')
                      << "checkpoint exploratory-host-doorbell bits=" << std::setw(8)
                      << value << " state=" << std::setw(8) << core.read32(0x1320)
                      << "\n" << std::flush;
            std::fprintf(stream, "%08x\n", core.read32(0x1320));
        } else if (line[0] == 'F' &&
                   (line[1] == '\n' || line[1] == '\0')) {
            // Opt-in copy of the observed stock 128-byte health DMA1.
            enableExploratoryStockFollowupDma1();
            std::fputs("00000001\n", stream);
        } else if (line[0] == 'L' && (line[1] == '\n' || line[1] == '\0')) {
            std::fprintf(stream, "%08x\n", exploratoryIspLoadedHighWater());
        } else if (line[0] == 'K' &&
                   std::sscanf(line, "K %x %u", &addr, &size) == 2) {
            uint16_t words[64];
            if (!readExploratoryIspRisc(addr, size, words)) {
                std::fputs("ERR\n", stream);
            } else {
                for (unsigned i = 0; i < size; ++i)
                    std::fprintf(stream, "%04x", words[i]);
                std::fputc('\n', stream);
            }
        } else if (line[0] == 'H' &&
                   std::sscanf(line, "H %x %x", &addr, &value) == 2 &&
                   (addr == 0x1004 || addr == 0x1204)) {
            setExploratoryPciWriteFromHost(true);
            core.write32(addr, value);
            setExploratoryPciWriteFromHost(false);
            std::cout << std::hex << std::setfill('0')
                      << "checkpoint host-pci-command local=" << std::setw(8) << addr
                      << " value=" << std::setw(8) << value << "\n" << std::flush;
            std::fprintf(stream, "%08x\n", core.read32(addr));
        } else if (line[0] == 'Y' && (line[1] == '\n' || line[1] == '\0')) {
            // Primary PCI configuration-retry state for the host model:
            // bit 0 modeled, bit 1 released, bits 16..31 current EBCR.
            const auto retry = exploratoryConfigRetryState();
            std::fprintf(stream, "%08x\n",
                         (retry.modeled ? 1u : 0u) | (retry.released ? 2u : 0u) |
                         (static_cast<unsigned>(retry.ebcr) << 16));
        } else if (line[0] == 'Q' && (line[1] == '\n' || line[1] == '\0')) {
            // Diagnostic only: pending MU status after the local mask. The
            // 80303 interrupt router and i960 service path remain unmodeled.
            std::fprintf(stream, "%08x\n", inboundMuUnmaskedStatus());
        } else if (line[0] == 'U' &&
                   std::sscanf(line, "U %x", &addr) == 1) {
            std::array<uint8_t, 4> bytes{};
            if (!readExploratoryHostDmaOutput(addr, bytes.data(), bytes.size())) {
                std::fputs("ERR\n", stream);
            } else {
                uint32_t word;
                std::memcpy(&word, bytes.data(), sizeof(word));
                std::fprintf(stream, "%08x\n", word);
            }
        } else if (line[0] == 'A' &&
                   std::sscanf(line, "A %x", &value) == 1 &&
                   (value & ~3u) == 0) {
            acknowledgeExploratoryOutboundDoorbell(value);
            std::fprintf(stream, "%08x\n", core.read32(0x132c));
        } else if (line[0] == 'P' && (line[1] == '\n' || line[1] == '\0')) {
            // Low byte: CPU priority; bit 8: global interrupt enable.
            std::fprintf(stream, "%08x\n",
                         static_cast<unsigned>(core.currentPriority()) |
                         (core.interruptsEnabled() ? 0x100u : 0u));
        } else if (line[0] == 'V' && (line[1] == '\n' || line[1] == '\0')) {
            std::fprintf(stream, "%08x\n", core.currentInterruptTable());
        } else if ((line[0] == 'I' || line[0] == 'C') &&
                   std::sscanf(line, "%c %x %x", &op, &addr, &value) >= 2 &&
                   (addr == 0x1310 || addr == 0x1314 || addr == 0x1320 ||
                    addr == 0x1324 || addr == 0x1328 ||
                    (op == 'C' && addr == 0x12a8) ||
                    // Offline PIRSR counterfactual; never forwarded to a card.
                    (op == 'C' && addr == 0x1050 && value <= 15) ||
                    (op == 'C' && (addr == 0xff008500 ||
                                   addr == 0xff000300 || addr == 0xff000304 ||
                                   addr == 0xff000308)) ||
                   (op == 'I' && (addr == 0x1004 || addr == 0x1204 ||
                                   addr == 0x1050 ||
                                   addr == 0x1318 || addr == 0x131c ||
                                   addr == 0x132c ||
                                   addr == 0x1404 || addr == 0x1444 ||
                                   addr == 0x1440 || addr == 0x1450 ||
                                   addr == 0x12a8 || addr == 0x12b0 ||
                                   addr == 0xff008500 || addr == 0xff008504 ||
                                   addr == 0xff008510 || addr == 0xff008520 ||
                                   addr == 0xff008524 || addr == 0xff008528 ||
                                   (addr >= 0xff000300 && addr <= 0xff000318 &&
                                    (addr & 3u) == 0))))) {
            if (op == 'C') {
                setExploratoryPciWriteFromHost(true);
                core.write32(addr, value);
                setExploratoryPciWriteFromHost(false);
            }
            std::fprintf(stream, "%08x\n", core.read32(addr));
        } else if (std::sscanf(line, "%c %x %u %x", &op, &addr, &size, &value) != 4 ||
            (op != 'R' && op != 'W') || (size != 1 && size != 2 && size != 4) ||
            !((addr >= 0xc0000000u && addr <= 0xc0ffffffu - size + 1) ||
              (model_s3_flash && op == 'R' && size == 4 &&
               addr >= 0xfef00000u && addr <= 0xff000000u - 4u) ||
              (model_s3_flash && op == 'R' && size == 4 &&
               addr == 0xe0500000u) ||
              exploratoryHostGuestWindowContains(addr, size) ||
              (addr >= 0x8bf00000u && addr <= 0x8bf000ffu - size + 1 &&
               size == 2 && !(addr & 1u))) ||
            ((addr & 3u) + size > 4)) {
            std::fputs("ERR\n", stream);
        } else {
            if (addr >= 0x8bf00000u && addr <= 0x8bf000ffu) {
                if (op == 'W') core.write16(addr, static_cast<ShortOrdinal>(value));
                std::fprintf(stream, "%08x\n", core.read16(addr));
                std::fflush(stream);
                continue;
            }
            const unsigned aligned = addr & ~3u;
            const unsigned shift = (addr & 3u) * 8;
            const uint32_t mask = size == 4 ? 0xffffffffu : ((1u << (size * 8)) - 1);
            uint32_t old = core.read32(aligned);
            if (op == 'W') core.write32(aligned, (old & ~(mask << shift)) | ((value & mask) << shift));
            std::fprintf(stream, "%08x\n", op == 'R' ? (old >> shift) & mask : value & mask);
        }
        std::fflush(stream);
    }
    fclose(stream);
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: accele160-emu IMAGE [MAX_CYCLES] [--strict] [--board-id=N] [--diagnose-loader] [--quiet-trace] [--trace-board-context] [--dump-aperture=PATH] [--bridge-socket=PATH] [--watch-mailbox] [--explore-timer-clock] [--explore-timer-interrupt] [--explore-qlogic-pci] [--explore-isp-mailbox] [--explore-isp-execute-ack] [--explore-isp-about-ack] [--explore-isp-queue-ack] [--explore-isp-retry-ack] [--trace-pci-registers] [--model-config-retry] [--explore-isp-reset-delay-ack] [--explore-isp-active-negation-ack] [--explore-isp-feature-ack] [--explore-isp-status-zero] [--explore-isp-init-id-ack] [--explore-isp-bus-reset-ack] [--explore-isp-target0-ack] [--explore-isp-target-sweep] [--explore-native-ring-dma1] [--explore-native-ring-health-dma1]\n";
        return 2;
    }
    bool strict = false;
    bool diagnose_loader = false;
    bool quiet_trace = false;
    bool watch_mailbox = false;
    bool exploratory_timer_clock = false;
    bool exploratory_timer_interrupt = false;
    bool exploratory_qlogic_pci = false;
    bool exploratory_isp_mailbox = false;
    bool exploratory_isp_execute_ack = false;
    bool exploratory_isp_about_ack = false;
    bool exploratory_isp_queue_ack = false;
    bool exploratory_isp_retry_ack = false;
    bool trace_pci_registers = false;
    bool model_config_retry = false;
    bool model_s3_flash = false;
    unsigned model_s3_fault = 0;
    bool retry_pin_high = true;
    bool exploratory_isp_reset_delay_ack = false;
    bool exploratory_isp_active_negation_ack = false;
    bool exploratory_isp_feature_ack = false;
    bool exploratory_isp_status_zero = false;
    bool exploratory_isp_init_id_ack = false;
    bool exploratory_isp_bus_reset_ack = false;
    bool exploratory_isp_target0_ack = false;
    bool exploratory_isp_target_sweep = false;
    bool exploratory_isp_no_device_auto = false;
    bool exploratory_native_ring_dma1 = false;
    bool exploratory_native_ring_health_dma1 = false;
    bool exploratory_native_ring_pdev_dma1 = false;
    bool trace_scan_state3 = false;
    bool trace_priority = false;
    bool trace_board_context = false;
    std::string aperture_path;
    std::string bridge_path;
    int board_id = -1;
    uint64_t max_cycles = 256;
    int option_start = 2;
    try {
        if (argc >= 3 && argv[2][0] != '-') {
            max_cycles = std::stoull(argv[2]);
            option_start = 3;
        }
    } catch (const std::exception&) {
        std::cerr << "invalid cycle count\n"; return 2;
    }
    for (int i = option_start; i < argc; ++i) {
        if (std::strcmp(argv[i], "--strict") == 0) strict = true;
        else if (std::strcmp(argv[i], "--diagnose-loader") == 0) diagnose_loader = true;
        else if (std::strcmp(argv[i], "--quiet-trace") == 0) quiet_trace = true;
        else if (std::strncmp(argv[i], "--dump-aperture=", 16) == 0) {
            aperture_path = argv[i] + 16;
            if (aperture_path.empty()) { std::cerr << "empty aperture path\n"; return 2; }
        }
        else if (std::strncmp(argv[i], "--bridge-socket=", 16) == 0) {
            bridge_path = argv[i] + 16;
            if (bridge_path.empty()) { std::cerr << "empty bridge path\n"; return 2; }
        }
        else if (std::strcmp(argv[i], "--watch-mailbox") == 0) watch_mailbox = true;
        else if (std::strcmp(argv[i], "--explore-timer-clock") == 0)
            exploratory_timer_clock = true;
        else if (std::strcmp(argv[i], "--explore-timer-interrupt") == 0) {
            exploratory_timer_clock = true;
            exploratory_timer_interrupt = true;
        }
        else if (std::strcmp(argv[i], "--explore-qlogic-pci") == 0)
            exploratory_qlogic_pci = true;
        else if (std::strcmp(argv[i], "--explore-isp-mailbox") == 0)
            exploratory_isp_mailbox = true;
        else if (std::strcmp(argv[i], "--explore-isp-execute-ack") == 0)
            exploratory_isp_execute_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-about-ack") == 0)
            exploratory_isp_about_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-queue-ack") == 0)
            exploratory_isp_queue_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-retry-ack") == 0)
            exploratory_isp_retry_ack = true;
        else if (std::strcmp(argv[i], "--trace-pci-registers") == 0)
            trace_pci_registers = true;
        else if (std::strcmp(argv[i], "--model-config-retry") == 0)
            model_config_retry = true;
        else if (std::strcmp(argv[i], "--model-s3-flash") == 0)
            model_s3_flash = true;
        else if (std::strcmp(argv[i], "--model-s3-fault=gate-stuck-off") == 0)
            model_s3_fault = 1;
        else if (std::strcmp(argv[i], "--model-s3-fault=low-vpp") == 0)
            model_s3_fault = 2;
        else if (std::strcmp(argv[i], "--model-s3-fault=wrong-id") == 0)
            model_s3_fault = 3;
        else if (std::strcmp(argv[i], "--model-s3-fault=locked-block") == 0)
            model_s3_fault = 4;
        else if (std::strcmp(argv[i], "--model-s3-fault=program-stuck") == 0)
            model_s3_fault = 5;
        else if (std::strcmp(argv[i], "--model-config-retry-low") == 0) {
            model_config_retry = true;
            retry_pin_high = false;
        }
        else if (std::strcmp(argv[i], "--explore-isp-reset-delay-ack") == 0)
            exploratory_isp_reset_delay_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-active-negation-ack") == 0)
            exploratory_isp_active_negation_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-feature-ack") == 0)
            exploratory_isp_feature_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-status-zero") == 0)
            exploratory_isp_status_zero = true;
        else if (std::strcmp(argv[i], "--explore-isp-init-id-ack") == 0)
            exploratory_isp_init_id_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-bus-reset-ack") == 0)
            exploratory_isp_bus_reset_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-target0-ack") == 0)
            exploratory_isp_target0_ack = true;
        else if (std::strcmp(argv[i], "--explore-isp-target-sweep") == 0)
            exploratory_isp_target_sweep = true;
        else if (std::strcmp(argv[i], "--explore-isp-no-device-auto") == 0)
            exploratory_isp_no_device_auto = true;
        else if (std::strcmp(argv[i], "--explore-native-ring-dma1") == 0)
            exploratory_native_ring_dma1 = true;
        else if (std::strcmp(argv[i], "--explore-native-ring-health-dma1") == 0)
            exploratory_native_ring_health_dma1 = true;
        else if (std::strcmp(argv[i], "--explore-native-ring-pdev-dma1") == 0)
            exploratory_native_ring_pdev_dma1 = true;
        else if (std::strcmp(argv[i], "--trace-scan-state3") == 0)
            trace_scan_state3 = true;
        else if (std::strcmp(argv[i], "--trace-priority") == 0)
            trace_priority = true;
        else if (std::strcmp(argv[i], "--trace-board-context") == 0)
            trace_board_context = true;
        else if (std::strncmp(argv[i], "--board-id=", 11) == 0) {
            try { board_id = std::stoi(argv[i] + 11); }
            catch (const std::exception&) {
                std::cerr << "invalid board-id\n"; return 2;
            }
            if (board_id < 0 || board_id > 31) {
                std::cerr << "board-id must be 0..31\n"; return 2;
            }
        } else { std::cerr << "unknown option\n"; return 2; }
    }
    if (exploratory_isp_execute_ack && !exploratory_isp_mailbox) {
        std::cerr << "execute acknowledgment requires --explore-isp-mailbox\n";
        return 2;
    }
    if (exploratory_isp_about_ack && !exploratory_isp_execute_ack) {
        std::cerr << "about acknowledgment requires --explore-isp-execute-ack\n";
        return 2;
    }
    if (exploratory_isp_queue_ack && !exploratory_isp_about_ack) {
        std::cerr << "queue acknowledgment requires --explore-isp-about-ack\n";
        return 2;
    }
    if (exploratory_isp_retry_ack && !exploratory_isp_queue_ack) {
        std::cerr << "retry acknowledgment requires --explore-isp-queue-ack\n";
        return 2;
    }
    if (exploratory_isp_reset_delay_ack && !exploratory_isp_retry_ack) {
        std::cerr << "reset-delay acknowledgment requires --explore-isp-retry-ack\n";
        return 2;
    }
    if (exploratory_isp_active_negation_ack && !exploratory_isp_reset_delay_ack) {
        std::cerr << "active-negation acknowledgment requires --explore-isp-reset-delay-ack\n";
        return 2;
    }
    if (exploratory_isp_feature_ack && !exploratory_isp_active_negation_ack) {
        std::cerr << "feature acknowledgment requires --explore-isp-active-negation-ack\n";
        return 2;
    }
    if (exploratory_isp_status_zero && !exploratory_isp_feature_ack) {
        std::cerr << "--explore-isp-status-zero requires --explore-isp-feature-ack\n";
        return 2;
    }
    if (exploratory_isp_init_id_ack && !exploratory_isp_status_zero) {
        std::cerr << "--explore-isp-init-id-ack requires --explore-isp-status-zero\n";
        return 2;
    }
    if (exploratory_isp_bus_reset_ack && !exploratory_isp_init_id_ack) {
        std::cerr << "--explore-isp-bus-reset-ack requires --explore-isp-init-id-ack\n";
        return 2;
    }
    if (exploratory_isp_target0_ack && !exploratory_isp_bus_reset_ack) {
        std::cerr << "--explore-isp-target0-ack requires --explore-isp-bus-reset-ack\n";
        return 2;
    }
    if (exploratory_isp_target_sweep && !exploratory_isp_target0_ack) {
        std::cerr << "--explore-isp-target-sweep requires --explore-isp-target0-ack\n";
        return 2;
    }
    if (exploratory_isp_no_device_auto && !exploratory_isp_target_sweep) {
        std::cerr << "--explore-isp-no-device-auto requires --explore-isp-target-sweep\n";
        return 2;
    }
    if (strict && (board_id >= 0 || exploratory_qlogic_pci)) {
        std::cerr << "board overrides require exploratory mode\n"; return 2;
    }
    std::ifstream input(argv[1], std::ios::binary);
    if (!input) { std::cerr << "cannot open image\n"; return 2; }
    std::vector<char> image((std::istreambuf_iterator<char>(input)), {});
    if (image.size() != 0x100000) {
        std::cerr << "expected exactly 1 MiB flash\n";
        return 2;
    }
    if (max_cycles > 100000000) { std::cerr << "cycle limit too high\n"; return 2; }
    constexpr uint32_t rom_base = 0xfef00000;
    constexpr uint32_t ram_base = 0xc0000000;
    constexpr uint32_t ram_size = 0x01000000;
    constexpr size_t ibr = 0xfff30;
    const uint32_t entry = word(image, ibr + 16);
    const uint32_t prcb = word(image, ibr + 20);
    const uint32_t checksum = word(image, ibr + 16) + word(image, ibr + 20) + word(image, ibr + 24);
    if (checksum || entry < rom_base || entry >= rom_base + image.size() ||
        prcb < rom_base || prcb >= rom_base + image.size()) {
        std::cerr << "invalid 80303 reset record\n";
        return 2;
    }
    Core core;
    if (model_s3_fault && !model_s3_flash) {
        std::cerr << "S3 fault requires --model-s3-flash\n";
        return 2;
    }
    core.begin();
    installToMainMemory(rom_base, image.data(), image.size());
    resetBoardMemoryAudit();
    resetInboundMu();
    if (exploratory_native_ring_dma1) enableExploratoryNativeRingDma1();
    if (exploratory_native_ring_health_dma1)
        enableExploratoryNativeRingHealthDma1();
    if (exploratory_native_ring_pdev_dma1)
        enableExploratoryNativeRingPdevDma1();
    resetExploratoryTimer0();
    setExploratoryBoardSelector(board_id);
    setExploratoryS3Flash(model_s3_flash);
    setExploratoryS3FlashFault(model_s3_fault);
    setExploratoryQlogicPci(exploratory_qlogic_pci);
    setExploratoryIspMailbox(exploratory_isp_mailbox);
    setExploratoryIspExecuteAck(exploratory_isp_execute_ack);
    setExploratoryIspAboutAck(exploratory_isp_about_ack);
    setExploratoryIspQueueAck(exploratory_isp_queue_ack);
    setExploratoryIspRetryAck(exploratory_isp_retry_ack);
    setExploratoryIspResetDelayAck(exploratory_isp_reset_delay_ack);
    setExploratoryIspActiveNegationAck(exploratory_isp_active_negation_ack);
    setExploratoryIspFeatureAck(exploratory_isp_feature_ack);
    setExploratoryIspStatusZero(exploratory_isp_status_zero);
    setExploratoryIspInitIdAck(exploratory_isp_init_id_ack);
    setExploratoryIspBusResetAck(exploratory_isp_bus_reset_ack);
    setExploratoryIspTarget0Ack(exploratory_isp_target0_ack);
    setExploratoryIspTargetSweep(exploratory_isp_target_sweep);
    // The real reset block establishes its own FP and SP in its first two
    // instructions. sim5's generic Kx start() uses a different boot record.
    core.resetAt(entry, prcb);
    setExploratoryPciRegisterTrace(trace_pci_registers);
    applyExploratoryConfigRetryStrap(model_config_retry, retry_pin_high);
    // Control-table prefetch is a reset-time hardware action, not a firmware
    // MMIO access for the exploratory unknown-peripheral audit.
    resetBoardMemoryAudit();
    std::cout << std::hex << std::setfill('0')
              << "ibr entry=" << std::setw(8) << entry
              << " prcb=" << std::setw(8) << prcb << "\n";
    Address previous_ip = 0;
    unsigned same_ip_count = 0;
    uint64_t mailbox_poll_hits = 0, mailbox_copy_hits = 0, mailbox_completion_hits = 0;
    uint64_t hardware_dispatch_hits = 0, hardware_receive_hits = 0;
    uint64_t menu_entry_hits = 0, mailbox_setup_hits = 0;
    uint64_t mailbox_mask_set_hits = 0, mailbox_mask_clear_hits = 0;
    uint64_t init_entry_hits = 0, board_callback_hits = 0, mu_init_hits = 0;
    uint64_t runtime_callback_hits = 0;
    uint64_t runtime_prompt_hits = 0;
    unsigned startup_priority_changes = 0;
    std::unordered_map<Address, uint64_t> runtime_samples;
    for (uint64_t n = 0; n < max_cycles; ++n) {
        const auto ip = core.currentIP();
        const auto prior_ip = previous_ip;
        g_trace_cycle = n;
        noteExploratoryTraceCycle(n, ip);
        same_ip_count = ip == previous_ip ? same_ip_count + 1 : 0;
        previous_ip = ip;
        if (same_ip_count == 256) {
            dumpAperture(core, aperture_path);
            printNativeReport(core);
            printAudit();
            std::cout << "stop cycle=" << std::dec << n << " reason=self-loop ip="
                      << std::hex << std::setw(8) << ip << "\n";
            serveBridge(core, bridge_path, exploratory_timer_clock,
                        exploratory_timer_interrupt, exploratory_isp_no_device_auto,
                        trace_scan_state3,
                        trace_priority, model_s3_flash);
            return 1;
        }
        const bool in_rom = ip >= rom_base && ip < rom_base + image.size();
        const bool in_ram = ip >= ram_base && ip < ram_base + ram_size;
        if ((!in_rom && !in_ram) || (ip & 3)) {
            printAudit();
            std::cout << "stop cycle=" << std::dec << n << " reason=unmapped-execute ip="
                      << std::hex << std::setw(8) << ip << "\n";
            return 1;
        }
        if (!quiet_trace)
            std::cout << "trace cycle=" << std::dec << n << " ip=" << std::hex
                      << std::setw(8) << ip << " insn=" << std::setw(8)
                      << core.read32(ip) << "\n";
        traceStockInterruptSetup(core);
        if (watch_mailbox) {
            if (ip == 0xc004d640) ++init_entry_hits;
            if (ip == 0xc004d700) ++board_callback_hits;
            if (ip == 0xc004d7a0) ++mu_init_hits;
            if (ip == 0xc00103f0) {
                ++menu_entry_hits;
                if (menu_entry_hits <= 4)
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint menu-entry cycle=" << std::dec << n
                              << " caller=" << std::hex << std::setw(8) << prior_ip
                              << "\n";
            }
            if (ip == 0xc004e450) ++mailbox_setup_hits;
            if (ip == 0xc00533c0) ++mailbox_mask_set_hits;
            if (ip == 0xc004d7fc) ++mailbox_mask_clear_hits;
            if ((n & 63u) == 0 && ip >= 0xc0010000 && ip < 0xc0100000)
                ++runtime_samples[ip];
            if (ip == 0xc00103f0 && ++runtime_prompt_hits <= 4)
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint runtime-prompt cycle=" << std::dec << n
                          << " rip=" << std::hex << std::setw(8) << core.readGPR(2)
                          << " fp=" << std::setw(8) << core.readGPR(31)
                          << " depth=" << std::dec << core.callDepth() << "\n";
            if (ip == 0xc004fa50) ++mailbox_poll_hits;
            if (ip == 0xc004fa7c) ++mailbox_copy_hits;
            if (ip == 0xc004e7dc) ++mailbox_completion_hits;
            if (ip == 0xc004e870) ++hardware_dispatch_hits;
            if (ip == 0xc004e660) ++hardware_receive_hits;
            if (ip == 0xc00103fc || ip == 0xc001042c) {
                ++runtime_callback_hits;
                if (runtime_callback_hits <= 6) {
                    uint32_t context = core.read32(0xc04ad650);
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint runtime-callback cycle=" << std::dec << n
                              << " ip=" << std::hex << std::setw(8) << ip
                              << " context=" << std::setw(8) << context
                              << " target=" << std::setw(8) << core.readGPR(0)
                              << " callback-a=" << std::setw(8) << core.read32(context + 0x254)
                              << " callback-b=" << std::setw(8) << core.read32(context + 0x25c)
                              << "\n";
                }
            }
            if ((ip == 0xc004fa50 && mailbox_poll_hits <= 3) ||
                (ip == 0xc004fa7c && mailbox_copy_hits <= 3)) {
                uint32_t queue = core.read32(0xc03e5bd0);
                uint32_t pointer = queue >= 0xc0000000 && queue < 0xc0ffffe8
                    ? core.read32(queue + 0xc) : 0;
                uint32_t first = pointer >= 0xc0000000 && pointer < 0xc0fffffc
                    ? core.read32(pointer) : 0;
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint mailbox-watch cycle=" << std::dec << n
                          << " ip=" << std::hex << std::setw(8) << ip
                          << " queue=" << std::setw(8) << queue
                          << " ring=" << std::setw(8) << pointer
                          << " first=" << std::setw(8) << first << "\n";
            }
        }
        if (ip == 0xc004cf70)
            std::cout << "checkpoint stock-runtime-entry cycle=" << std::dec
                      << n << " ip=c004cf70\n";
        if (ip == 0xc000a840) {
            std::cout << "checkpoint loader-checksum computed=" << std::setw(8)
                      << core.readGPR(17) << " stored=" << std::setw(8)
                      << core.readGPR(18) << "\n";
        }
        if (ip == 0xc000a7f0 || ip == 0xc000a7f4 || ip == 0xc000a810) {
            std::cout << "checkpoint crc-memory ip=" << std::setw(8) << ip
                      << " accumulator=" << std::setw(8)
                      << core.read32(0xc04ad640) << "\n";
        }
        if (ip == 0xc000a8e4) {
            std::cout << "checkpoint huffman-count generated=" << std::setw(8)
                      << core.readGPR(4) << " required=" << std::setw(8)
                      << core.readGPR(6) << "\n";
        }
        if (diagnose_loader && ip == 0xc000a860) {
            const auto source = core.read32(0xc04ad62c);
            std::cout << "checkpoint table-input source=" << std::setw(8)
                      << source << " remaining=" << std::setw(8)
                      << core.read32(0xc04ad644) << " refill=" << std::setw(8)
                      << core.read32(0xc04ad638) << " data=";
            for (unsigned i = 0; i < 4; ++i)
                std::cout << " " << std::setw(8) << core.read32(source + i * 4);
            std::cout << "\n";
        }
        if (diagnose_loader && ip == 0xc000a894) {
            std::cout << "checkpoint table-pair word=" << std::setw(8)
                      << core.read32(0xc04a25a4)
                      << " made=" << std::setw(8) << core.readGPR(4)
                      << " pairs-left=" << std::setw(8) << core.readGPR(5)
                      << " source=" << std::setw(8) << core.read32(0xc04ad62c)
                      << "\n";
        }
        if (ip == 0xc0010d40 || ip == 0xc0010d50 ||
            ip == 0xc0012730 || ip == 0xc0010320) {
            std::cout << std::hex << "checkpoint frame ip=" << std::setw(8) << ip
                      << " pfp=" << std::setw(8) << core.readGPR(0)
                      << " sp=" << std::setw(8) << core.readGPR(1)
                      << " rip=" << std::setw(8) << core.readGPR(2)
                      << " fp=" << std::setw(8) << core.readGPR(31)
                      << " depth=" << std::dec
                      << core.callDepth() << "\n";
        }
        if (ip == 0xc00139f0 || ip == 0xc0013a1c ||
            ip == 0xc0013a50 || ip == 0xc0013a70) {
            std::cout << std::hex << "checkpoint init-tasks ip=" << std::setw(8)
                      << ip << " count=" << std::setw(8)
                      << core.read32(0xc001c1c0) << " table=" << std::setw(8)
                      << core.read32(0xc001c230) << " heir=" << std::setw(8)
                      << core.read32(0xc001c050) << " status=" << std::setw(8)
                      << core.readGPR(16) << " id=" << std::setw(8)
                      << core.read32(core.readGPR(31) + 0x40) << "\n";
        }
        if (ip == 0xc0010d50) {
            printNativeReport(core);
        }
        if (ip == 0xc0010300) {
            std::cout << std::hex << "checkpoint context-save address="
                      << std::setw(8) << core.readGPR(16)
                      << " pfp=" << std::setw(8) << core.readGPR(0)
                      << " sp=" << std::setw(8) << core.readGPR(1) << "\n";
        }
        if (ip == 0xc0010314) {
            const auto source = core.readGPR(17);
            std::cout << std::hex << "checkpoint context-restore address="
                      << std::setw(8) << source
                      << " pfp=" << std::setw(8) << core.read32(source)
                      << " sp=" << std::setw(8) << core.read32(source + 4)
                      << " target-rip=" << std::setw(8)
                      << core.read32(core.read32(source) + 8)
                      << "\n";
        }
        const auto priority_before = trace_priority ? core.currentPriority() : 0;
        const auto board_before = trace_board_context
            ? boardContextKind(core) : std::pair<uint32_t, uint32_t>{};
        core.cycle();
        if (trace_board_context) {
            const auto board_after = boardContextKind(core);
            if (board_before != board_after)
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint board-context-change cycle=" << std::dec
                          << n << " ip=" << std::hex << std::setw(8) << ip
                          << " context-before=" << std::setw(8) << board_before.first
                          << " kind-before=" << std::setw(8) << board_before.second
                          << " context-after=" << std::setw(8) << board_after.first
                          << " kind-after=" << std::setw(8) << board_after.second
                          << "\n" << std::flush;
        }
        if (trace_priority && priority_before != core.currentPriority() &&
            startup_priority_changes++ < 64)
            std::cout << std::hex << std::setfill('0')
                      << "checkpoint startup-priority-change cycle=" << std::dec
                      << n << " ip=" << std::hex << std::setw(8) << ip
                      << " next=" << std::setw(8) << core.currentIP()
                      << std::dec << " before="
                      << static_cast<unsigned>(priority_before) << " after="
                      << static_cast<unsigned>(core.currentPriority())
                      << "\n" << std::flush;
        if (exploratory_timer_clock) advanceExploratoryBusClock();
        if (exploratory_timer_interrupt && core.lastFault() == NoFault &&
            deliverExploratoryTimer0(core) && watch_mailbox)
            std::cout << "checkpoint timer0-interrupt ip=" << std::hex
                      << std::setw(8) << core.currentIP() << " cycle="
                      << std::dec << n << "\n";
        if (ip == 0xc0010320) {
            std::cout << std::hex << "checkpoint context-after-ret ip="
                      << std::setw(8) << core.currentIP()
                      << " rip=" << std::setw(8) << core.readGPR(2)
                      << " fp=" << std::setw(8) << core.readGPR(31)
                      << " pfp=" << std::setw(8) << core.readGPR(0) << "\n";
        }
        if (strict) {
            const auto audit = getBoardMemoryAudit();
            if (audit.unknown_read || audit.unknown_write) {
                printAudit();
                std::cout << "stop cycle=" << std::dec << n
                          << " reason=unmodeled-peripheral\n";
                return 1;
            }
        }
        if (core.lastFault() != NoFault) {
            printAudit();
            std::cout << "stop cycle=" << std::dec << n << " reason=cpu-fault code="
                      << std::hex << std::setw(8) << core.lastFault()
                      << " ip=" << std::setw(8) << ip
                      << " pfp=" << std::setw(8) << core.readGPR(0)
                      << " sp=" << std::setw(8) << core.readGPR(1)
                      << " rip=" << std::setw(8) << core.readGPR(2)
                      << " fp=" << std::setw(8) << core.readGPR(31)
                      << " depth=" << std::dec << core.callDepth() << "\n";
            return 1;
        }
    }
    dumpAperture(core, aperture_path);
    if (watch_mailbox)
        std::cout << std::dec << "checkpoint mailbox-watch-count hardware-dispatch="
                  << hardware_dispatch_hits << " hardware-receive=" << hardware_receive_hits
                  << " ring-poll=" << mailbox_poll_hits
                  << " copy=" << mailbox_copy_hits
                  << " completion=" << mailbox_completion_hits << "\n";
        std::cout << "checkpoint firmware-path-count menu=" << menu_entry_hits
                  << " mu-setup=" << mailbox_setup_hits
                  << " mu-mask-set=" << mailbox_mask_set_hits
                  << " mu-mask-clear=" << mailbox_mask_clear_hits
                  << " init-entry=" << init_entry_hits
                  << " board-callback=" << board_callback_hits
                  << " mu-init=" << mu_init_hits << "\n";
    if (watch_mailbox) {
        std::vector<std::pair<Address, uint64_t>> frequent(runtime_samples.begin(),
                                                           runtime_samples.end());
        std::sort(frequent.begin(), frequent.end(), [](const auto& a, const auto& b) {
            return a.second > b.second;
        });
        std::cout << std::hex << std::setfill('0')
                  << "checkpoint mailbox-state ip=" << std::setw(8) << core.currentIP()
                  << " queue=" << std::setw(8) << core.read32(0xc03e5bd0)
                  << " context=" << std::setw(8) << core.read32(0xc04ad650)
                  << " ring-index=" << std::setw(8) << core.read32(0xc00a7aa0)
                  << " event=" << std::setw(8) << core.read32(0x1320) << "\n";
        uint32_t queue = core.read32(0xc03e5bd0);
        uint32_t context = core.read32(0xc04ad650);
        const uint32_t ring = queue >= 0xc0000000 && queue < 0xc0fffff0
            ? core.read32(queue + 0xc) : 0;
        std::cout << "checkpoint mailbox-pointers ring=" << std::setw(8) << ring
                  << " ring-word=";
        if (ring >= 0xc0000000 && ring < 0xc0fffffc)
            std::cout << std::setw(8) << core.read32(ring);
        else
            std::cout << "unavailable";
        std::cout << " callback-a=" << std::setw(8) << core.read32(context + 0x254)
                  << " callback-b=" << std::setw(8) << core.read32(context + 0x25c)
                  << "\n";
        for (size_t i = 0; i < std::min<size_t>(frequent.size(), 12); ++i)
            std::cout << "checkpoint runtime-sample ip=" << std::setw(8)
                      << frequent[i].first << std::dec << " count=" << frequent[i].second
                      << "\n" << std::hex;
    }
    printAudit();
    std::cout << "stop cycle=" << std::dec << max_cycles << " reason=budget ip="
              << std::hex << std::setw(8) << core.currentIP() << "\n";
    serveBridge(core, bridge_path, exploratory_timer_clock,
                exploratory_timer_interrupt, exploratory_isp_no_device_auto,
                trace_scan_state3,
                trace_priority, model_s3_flash);
    return 0;
}
