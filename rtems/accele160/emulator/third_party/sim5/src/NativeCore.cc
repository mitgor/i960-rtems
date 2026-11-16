// sim5
// Copyright (c) 2022-2023, Joshua Scoggins
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#define _XOPEN_SOURCE 600
#include "Core.h"
#include "board_memory.h"
#include <string>
#include <iostream>
#include <iomanip>
#include <array>
#include <algorithm>
#include <cstring>
#include <stdexcept>
#include <thread>
#include <sstream>
#include <mutex>
#include <atomic>
#include <chrono>
#include <type_traits>
namespace {
    BoardMemoryAudit memoryAudit;
    int exploratoryBoardSelector = -1;
    bool exploratoryBoardSelectorWritten = false;
    bool exploratoryQlogicPci = false;
    bool exploratoryIspMailbox = false;
    bool exploratoryIspExecuteAck = false;
    bool exploratoryIspAboutAck = false;
    bool exploratoryIspQueueAck = false;
    bool exploratoryIspRetryAck = false;
    bool exploratoryIspResetDelayAck = false;
    bool exploratoryIspActiveNegationAck = false;
    bool exploratoryIspFeatureAck = false;
    bool exploratoryIspStatusZero = false;
    bool exploratoryIspInitIdAck = false;
    bool exploratoryIspBusResetAck = false;
    bool exploratoryIspTarget0Ack = false;
    bool exploratoryIspTargetSweep = false;
    bool ispExecuteAcknowledged = false;
    bool ispAboutAcknowledged = false;
    uint32_t ispRequestQueueBus = 0;
    uint32_t ispRequestQueueEntries = 0;
    uint32_t ispResponseQueueBus = 0;
    uint32_t ispResponseQueueEntries = 0;
    bool ispRetryAcknowledged = false;
    bool ispResetDelayAcknowledged = false;
    bool ispActiveNegationAcknowledged = false;
    bool ispFeatureAcknowledged = false;
    bool ispStatusZeroAcknowledged = false;
    bool ispInitIdAcknowledged = false;
    bool ispBusResetAcknowledged = false;
    unsigned ispNextTarget = 0;
    uint32_t ispMailboxCompletions = 0;
    uint32_t ispHccrTraces = 0;
    bool ispUnknownCommandTraced = false;
    std::array<ShortOrdinal, 65536> ispRiscRam{};
    uint32_t ispLoadedHighWater = 0;
    Ordinal secondaryPciSelector = 0;
    Ordinal secondaryPciData() noexcept {
        // SOCCAR uses one-hot IDSEL in bits 16..31. These five dwords were
        // captured directly from channel 0; no other device is asserted.
        if ((secondaryPciSelector & 0xffff0000u) != 0x00010000u)
            return 0xffffffffu;
        switch (secondaryPciSelector & 0xfcu) {
            case 0x00: return 0x10161077u;
            case 0x04: return 0x02b00006u;
            case 0x08: return 0x01000006u;
            case 0x10: return 0x00000001u;
            case 0x14: return 0xfff00000u;
            default: return 0; // unobserved present-device register
        }
    }
    struct InboundMu {
        Ordinal message[2]{};
        Ordinal doorbell = 0;
        Ordinal status = 0;
        Ordinal mask = 0xffffffffu;
    } inboundMu;
    struct HostDmaMailbox {
        Ordinal base = 0;
        std::array<uint8_t, 64> bytes{};
        bool valid = false;
    } hostDmaMailbox;
    struct HostDmaRingSlot {
        Ordinal base = 0;
        // The first five observed 64-byte command slots only.
        std::array<uint8_t, 320> bytes{};
        bool valid = false;
    } hostDmaRingSlot;
    struct HostGuestWindow {
        Ordinal base = 0;
        uint32_t length = 0;
        bool valid = false;
    } hostGuestStatus, hostGuestHealth, hostGuestOutput, hostGuestPdev,
      hostGuestSense, hostGuestScsiData;
    bool hostGuestOutputDmaCompleted = false;
    bool hostGuestHealthDmaCompleted = false;
    bool hostGuestPdevDmaCompleted = false;
    struct HostDmaOutput {
        Ordinal base = 0;
        std::array<uint8_t, 512> bytes{};
        uint32_t length = 0;
        bool valid = false;
        bool completed = false;
    } hostDmaOutput;
    bool exploratoryMuDmaTrace = false;
    bool exploratoryNativeRingDma1 = false;
    bool exploratoryNativeRingHealthDma1 = false;
    bool exploratoryNativeRingPdevDma1 = false;
    bool exploratoryStockFollowupDma1 = false;
    unsigned exploratoryMuDmaWrites = 0;
    unsigned exploratoryMuHostReads = 0;
    std::array<Ordinal, 3> dmaChannelStatus{};
    constexpr int dmaStatusIndex(Address address) noexcept {
        switch (address & ~Address{3}) {
            case 0x1404: return 0;
            case 0x1444: return 1;
            case 0x1484: return 2;
            default: return -1;
        }
    }
    struct Timer0 {
        Ordinal reload = 0;
        Ordinal count = 0;
        Ordinal mode = 0;
        unsigned prescaler = 0;
        uint64_t terminal_events = 0;
    } timer0;
    constexpr bool timer0Address(Address address) noexcept {
        return address == 0xff000300 || address == 0xff000304 ||
               address == 0xff000308;
    }
    Ordinal timer0Word(Address address) noexcept {
        switch (address) {
            case 0xff000300: return timer0.reload;
            case 0xff000304: return timer0.count;
            case 0xff000308: return timer0.mode;
            default: return 0;
        }
    }
    void storeTimer0Word(Address address, Ordinal value) noexcept {
        switch (address) {
            case 0xff000300: timer0.reload = value; break;
            case 0xff000304: timer0.count = value; break;
            case 0xff000308:
                timer0.mode = value & ~Ordinal{1};
                timer0.prescaler = 0;
                break;
            default: break;
        }
    }
    constexpr bool inboundMuAddress(Address address) noexcept {
        const Address word = address & ~Address{3};
        return word == 0x1310 || word == 0x1314 || word == 0x1320 ||
               word == 0x1324 || word == 0x1328;
    }
    Ordinal inboundMuWord(Address address) noexcept {
        switch (address & ~Address{3}) {
            case 0x1310: return inboundMu.message[0];
            case 0x1314: return inboundMu.message[1];
            case 0x1320: return inboundMu.doorbell;
            case 0x1324: return (inboundMu.status & ~Ordinal{4}) |
                                (inboundMu.doorbell ? 4u : 0u);
            case 0x1328: return inboundMu.mask;
            default: return 0;
        }
    }
    void storeInboundMuWord(Address address, Ordinal value) noexcept {
        switch (address & ~Address{3}) {
            case 0x1310: inboundMu.message[0] = value; break;
            case 0x1314: inboundMu.message[1] = value; break;
            case 0x1320: inboundMu.doorbell &= ~value; break;
            case 0x1324: inboundMu.status &= ~(value & 3u); break;
            case 0x1328: inboundMu.mask = value; break;
            default: break;
        }
    }
    constexpr bool backedByKnownMemory(Address address) noexcept {
        return address < 0x1000 ||
               (address >= 0xc0000000 && address < 0xc1000000) ||
               (address >= 0xfef00000 && address < 0xff000000);
    }
    void auditRead(Address address) noexcept {
        if (!backedByKnownMemory(address) && address != 0xe0600007 &&
            !memoryAudit.unknown_read) {
            memoryAudit.unknown_read = true;
            memoryAudit.first_read = address;
        }
    }
    template<typename T>
    bool modeledCoreWrite(Address address, T value) noexcept {
        if constexpr (sizeof(T) != 4) {
            return false;
        } else {
            auto word = static_cast<Ordinal>(value);
            switch (address) {
                case 0xff008500: // IPND, clear pending interrupts
                case 0xff008504: // IMSK, reset mask
                case 0xff008100: // DLMCON, reset local memory control
                    return word == 0;
                case 0xff008110: // LMAR1
                    return word == 0xc0400002;
                case 0xff008114: // LMMR1
                    return word == 0xffe00001;
                case 0xff00810c: // LMMR0
                    return word == 0xffc00001;
                case 0xff008108: // LMAR0
                    return word == 0xc0000002;
                case 0x0000154c: // FEBR0, first flash bank base
                    return word == 0xfef00000;
                case 0x00001550: // FEBR1, second bank base
                    return word == 0xe0000000;
                case 0x00001554: // FBSR0
                    return word == 5;
                case 0x00001558: // FBSR1
                    return word == 15;
                case 0x0000155c: // FWSR0
                case 0x00001560: // FWSR1
                    return word == 34;
                default:
                    return false;
            }
        }
    }
    template<typename T>
    void auditWrite(Address address, T value) noexcept {
        if (!backedByKnownMemory(address) &&
            address != 0xe0600007 && address != 0xe0600006 &&
            !modeledCoreWrite(address, value) &&
            !memoryAudit.unknown_write) {
            memoryAudit.unknown_write = true;
            memoryAudit.first_write = address;
        }
    }
    union Cell {
        ByteOrdinal bytes[16];
        ByteInteger byteIntegers[16];
        ShortOrdinal shortOrdinals[8];
        ShortInteger shortIntegers[8];
        Ordinal ordinals[4];
        Integer integers[4];
        LongOrdinal longOrdinals[2];
        LongInteger longIntegers[2];
        float reals[4];
        double realLongs[2];
        long double extendedReal;
        QuadOrdinal quadOrdinal;
#define X(type) \
        void setValue(Address address, type value , TreatAs < type > ) noexcept; \
        type getValue(Address address, TreatAs < type > ) const noexcept
        X(ByteOrdinal);
        X(ByteInteger);
        X(ShortOrdinal);
        X(ShortInteger);
        X(Ordinal);
        X(Integer);
        X(LongOrdinal);
        X(LongInteger);
        X(float);
        X(double);
        X(long double);
        X(QuadOrdinal);
#undef X
    };
    std::unique_ptr<uint8_t[]> physicalMemory;
    std::chrono::time_point startup = std::chrono::system_clock::now();
    //bool* tagBits = nullptr;
} // end namespace
void resetBoardMemoryAudit() noexcept { memoryAudit = {}; }
BoardMemoryAudit getBoardMemoryAudit() noexcept { return memoryAudit; }
void resetInboundMu() noexcept {
    inboundMu = {};
    inboundMu.mask = 0xffffffffu;
    hostDmaMailbox = {};
    hostDmaRingSlot = {};
    hostGuestStatus = {};
    hostGuestHealth = {};
    hostGuestOutput = {};
    hostGuestPdev = {};
    hostGuestSense = {};
    hostGuestScsiData = {};
    hostGuestOutputDmaCompleted = false;
    hostGuestHealthDmaCompleted = false;
    hostGuestPdevDmaCompleted = false;
    hostDmaOutput = {};
    exploratoryMuDmaTrace = false;
    exploratoryNativeRingDma1 = false;
    exploratoryNativeRingHealthDma1 = false;
    exploratoryNativeRingPdevDma1 = false;
    exploratoryStockFollowupDma1 = false;
    exploratoryMuDmaWrites = 0;
    exploratoryMuHostReads = 0;
    dmaChannelStatus = {};
}
void resetExploratoryTimer0() noexcept { timer0 = {}; }
uint64_t exploratoryTimer0Events() noexcept { return timer0.terminal_events; }
void advanceExploratoryBusClock() noexcept {
    if (!(timer0.mode & 2u)) return;
    const unsigned divisor = 1u << ((timer0.mode >> 4) & 3u);
    if (++timer0.prescaler < divisor) return;
    timer0.prescaler = 0;
    if (timer0.count == 0) return; // zero initial count is undefined on Jx
    if (--timer0.count != 0) return;
    ++timer0.terminal_events;
    // The core's internal register page is currently backed by the same
    // memory array. IPND bit 12 is TINT0 on the 80960Jx.
    *reinterpret_cast<Ordinal*>(physicalMemory.get() + 0xff008500u) |= 1u << 12;
    if (timer0.mode & 4u) timer0.count = timer0.reload;
    else timer0.mode &= ~Ordinal{2};
}
uint32_t inboundMuUnmaskedStatus() noexcept {
    return inboundMuWord(0x1324) & ~inboundMu.mask;
}
void postExploratoryInboundDoorbell(uint32_t bits) noexcept {
    inboundMu.doorbell |= bits;
}
bool submitInboundMailbox(uint64_t dma_address) noexcept {
    if (!dma_address || (dma_address & 3) || dma_address > 0xffffffffu ||
        inboundMu.doorbell & 1u)
        return false;
    inboundMu.message[0] = static_cast<Ordinal>(dma_address);
    inboundMu.message[1] = static_cast<Ordinal>(dma_address >> 32);
    inboundMu.status |= 3u;
    inboundMu.doorbell |= 1u;
    return true;
}
bool submitInboundMailboxPayload(uint64_t dma_address,
                                 const uint8_t* bytes, uint32_t length) noexcept {
    if (!bytes || length != hostDmaMailbox.bytes.size() ||
        !dma_address || (dma_address & 3) ||
        dma_address > uint64_t{0x100000000} - length ||
        (inboundMu.doorbell & 1u))
        return false;
    if (!submitInboundMailbox(dma_address)) return false;
    hostDmaMailbox.base = static_cast<Ordinal>(dma_address);
    std::copy_n(bytes, length, hostDmaMailbox.bytes.begin());
    hostDmaMailbox.valid = true;
    hostDmaRingSlot = {};
    hostGuestStatus = {};
    hostGuestHealth = {};
    hostGuestOutput = {};
    hostGuestPdev = {};
    hostGuestSense = {};
    hostGuestScsiData = {};
    hostGuestOutputDmaCompleted = false;
    hostGuestHealthDmaCompleted = false;
    hostGuestPdevDmaCompleted = false;
    hostDmaOutput = {};
    uint64_t output_bus = 0;
    for (unsigned i = 0; i < 8; ++i)
        output_bus |= uint64_t{bytes[32 + i]} << (i * 8);
    uint32_t output_length = 0;
    for (unsigned i = 0; i < 4; ++i)
        output_length |= uint32_t{bytes[40 + i]} << (i * 8);
    const uint32_t expected = bytes[21] == 0x01 || bytes[21] == 0x2d ? 512 :
                              bytes[21] == 0x11 || bytes[21] == 0xd0 ? 128 :
                              bytes[21] == 0x15 ? 64 : 0;
    if (output_bus && expected && output_length == expected &&
        output_bus <= uint64_t{0x100000000} - output_length) {
        hostDmaOutput.base = static_cast<Ordinal>(output_bus);
        hostDmaOutput.length = output_length;
        hostDmaOutput.valid = true;
    }
    return true;
}
bool stageExploratoryHostRingSlot(uint64_t dma_address,
                                  const uint8_t* bytes,
                                  uint32_t length) noexcept {
    uint64_t expected = 0;
    for (unsigned i = 0; i < 8; ++i)
        expected |= uint64_t{hostDmaMailbox.bytes[32 + i]} << (8 * i);
    if (!bytes || length != 64u ||
        !hostDmaMailbox.valid || hostDmaMailbox.bytes[21] != 0x8e ||
        dma_address < expected || dma_address > expected + 256u ||
        ((dma_address - expected) & 63u) ||
        dma_address < 0x00100000u || (expected & 0xfffu) ||
        dma_address + length > 0x20000000u ||
        (hostDmaMailbox.valid &&
         dma_address < uint64_t{hostDmaMailbox.base} + hostDmaMailbox.bytes.size() &&
         hostDmaMailbox.base < dma_address + length))
        return false;
    const uint32_t offset = static_cast<uint32_t>(dma_address - expected);
    if (offset && (!hostDmaRingSlot.valid || hostDmaRingSlot.base != expected))
        return false;
    if (!offset) {
        hostDmaRingSlot = {};
        hostDmaRingSlot.base = static_cast<Ordinal>(expected);
    }
    std::copy_n(bytes, length, hostDmaRingSlot.bytes.begin() + offset);
    hostDmaRingSlot.valid = true;
    return true;
}
bool registerExploratoryHostGuestWindow(char kind, uint64_t dma_address,
                                         uint32_t length) noexcept {
    if (!hostDmaMailbox.valid || !hostDmaRingSlot.valid ||
        dma_address < 0x00100000u || (dma_address & 3u) ||
        dma_address + length > 0x20000000u ||
        (dma_address < uint64_t{hostDmaRingSlot.base} + 64u &&
         hostDmaRingSlot.base < dma_address + length))
        return false;
    const unsigned offset = kind == 'S' ? 40 : kind == 'H' ? 24 :
                            kind == 'P' ? 160 : kind == 'T' ? 224 :
                            kind == 'U' ? 264 : kind == 'V' ? 288 : 32;
    const uint8_t* source = kind == 'O' || kind == 'P' || kind == 'T' ||
                            kind == 'U' || kind == 'V' ?
                            hostDmaRingSlot.bytes.data() :
                            hostDmaMailbox.bytes.data();
    uint64_t expected = 0;
    for (unsigned i = 0; i < 8; ++i)
        expected |= uint64_t{source[offset + i]} << (8 * i);
    const uint32_t expected_length = kind == 'S' ?
                                     (length == 8 || length == 24 ||
                                      length == 32 || length == 40 ? length : 0) :
                                     kind == 'H' ? 128 :
                                     kind == 'O' || kind == 'T' ? 1004 :
                                     kind == 'P' ? 512 :
                                     kind == 'U' ? 16 :
                                     kind == 'V' ? 36 : 0;
    if (!expected_length || length != expected_length ||
        dma_address != expected)
        return false;
    if (kind == 'O' || kind == 'P' || kind == 'T' ||
        kind == 'U' || kind == 'V') {
        auto disjoint = [](uint64_t a, uint64_t a_length,
                           uint64_t b, uint64_t b_length) noexcept {
            return a + a_length <= b || b + b_length <= a;
        };
        uint64_t status_base = 0, health_base = 0;
        for (unsigned i = 0; i < 8; ++i) {
            status_base |= uint64_t{hostDmaMailbox.bytes[40 + i]} << (8 * i);
            health_base |= uint64_t{hostDmaMailbox.bytes[24 + i]} << (8 * i);
        }
        if (!disjoint(dma_address, length, hostDmaRingSlot.base, 32768u) ||
            !disjoint(dma_address, length, status_base, 4096u) ||
            !disjoint(dma_address, length, health_base, 1024u) ||
            !disjoint(dma_address, length, hostDmaMailbox.base, 64u))
            return false;
        if ((kind == 'U' && hostGuestScsiData.valid &&
             !disjoint(dma_address, length, hostGuestScsiData.base,
                       hostGuestScsiData.length)) ||
            (kind == 'V' && hostGuestSense.valid &&
             !disjoint(dma_address, length, hostGuestSense.base,
                       hostGuestSense.length)))
            return false;
    }
    HostGuestWindow* window = kind == 'S' ? &hostGuestStatus :
                              kind == 'H' ? &hostGuestHealth :
                              kind == 'P' ? &hostGuestPdev :
                              kind == 'U' ? &hostGuestSense :
                              kind == 'V' ? &hostGuestScsiData :
                                            &hostGuestOutput;
    *window = {static_cast<Ordinal>(dma_address), length, true};
    if (kind == 'T') hostGuestOutputDmaCompleted = false;
    return true;
}
bool exploratoryHostGuestWindowContains(uint64_t dma_address,
                                        uint32_t length) noexcept {
    if (!length || dma_address + length > 0x20000000u)
        return false;
    if (hostDmaRingSlot.valid &&
        dma_address >= hostDmaRingSlot.base &&
        dma_address + length <= uint64_t{hostDmaRingSlot.base} +
                               hostDmaRingSlot.bytes.size())
        return true;
    for (const HostGuestWindow* window :
         {&hostGuestStatus, &hostGuestHealth, &hostGuestOutput,
          &hostGuestPdev, &hostGuestSense, &hostGuestScsiData})
        if (window->valid && dma_address >= window->base &&
            dma_address + length <= uint64_t{window->base} + window->length)
            return true;
    return false;
}
bool readExploratoryHostDma(uint64_t address, uint8_t* bytes,
                            uint32_t length) noexcept {
    if (!hostDmaMailbox.valid || !bytes ||
        address < hostDmaMailbox.base ||
        address - hostDmaMailbox.base > hostDmaMailbox.bytes.size() ||
        length > hostDmaMailbox.bytes.size() - (address - hostDmaMailbox.base))
        return false;
    std::copy_n(hostDmaMailbox.bytes.begin() +
                (address - hostDmaMailbox.base), length, bytes);
    return true;
}
bool readExploratoryHostDmaOutput(uint64_t address, uint8_t* bytes,
                                  uint32_t length) noexcept {
    if (!hostDmaOutput.completed || !bytes ||
        address < hostDmaOutput.base ||
        address - hostDmaOutput.base > hostDmaOutput.length ||
        length > hostDmaOutput.length - (address - hostDmaOutput.base))
        return false;
    std::copy_n(hostDmaOutput.bytes.begin() +
                (address - hostDmaOutput.base), length, bytes);
    return true;
}
void acknowledgeExploratoryOutboundDoorbell(uint32_t bits) noexcept {
    if (physicalMemory)
        *reinterpret_cast<Ordinal*>(physicalMemory.get() + 0x132c) &= ~bits;
}
uint32_t exploratoryHostDmaBase() noexcept {
    return hostDmaMailbox.valid ? hostDmaMailbox.base : 0;
}
void enableExploratoryMuDmaTrace() noexcept {
    exploratoryMuDmaTrace = true;
    exploratoryMuDmaWrites = 0;
    exploratoryMuHostReads = 0;
}
void enableExploratoryNativeRingDma1() noexcept {
    exploratoryNativeRingDma1 = true;
}
void enableExploratoryNativeRingHealthDma1() noexcept {
    exploratoryNativeRingHealthDma1 = true;
}
void enableExploratoryNativeRingPdevDma1() noexcept {
    exploratoryNativeRingPdevDma1 = true;
}
void enableExploratoryStockFollowupDma1() noexcept {
    exploratoryStockFollowupDma1 = true;
}
void setExploratoryBoardSelector(int value) noexcept {
    exploratoryBoardSelector = value;
    exploratoryBoardSelectorWritten = false;
}
void setExploratoryQlogicPci(bool enabled) noexcept {
    exploratoryQlogicPci = enabled;
    secondaryPciSelector = 0;
}
void setExploratoryIspMailbox(bool enabled) noexcept {
    exploratoryIspMailbox = enabled;
    ispMailboxCompletions = 0;
    ispHccrTraces = 0;
    ispUnknownCommandTraced = false;
    ispRiscRam.fill(0);
    ispLoadedHighWater = 0;
    ispExecuteAcknowledged = false;
    ispAboutAcknowledged = false;
    ispRequestQueueBus = 0;
    ispRequestQueueEntries = 0;
    ispResponseQueueBus = 0;
    ispResponseQueueEntries = 0;
    ispRetryAcknowledged = false;
    ispResetDelayAcknowledged = false;
    ispActiveNegationAcknowledged = false;
    ispInitIdAcknowledged = false;
    ispBusResetAcknowledged = false;
    ispNextTarget = 0;
}
void setExploratoryIspExecuteAck(bool enabled) noexcept {
    exploratoryIspExecuteAck = enabled;
}
void setExploratoryIspAboutAck(bool enabled) noexcept {
    exploratoryIspAboutAck = enabled;
}
void setExploratoryIspQueueAck(bool enabled) noexcept {
    exploratoryIspQueueAck = enabled;
}
void setExploratoryIspRetryAck(bool enabled) noexcept {
    exploratoryIspRetryAck = enabled;
}
void setExploratoryIspResetDelayAck(bool enabled) noexcept {
    exploratoryIspResetDelayAck = enabled;
}
void setExploratoryIspActiveNegationAck(bool enabled) noexcept {
    exploratoryIspActiveNegationAck = enabled;
}
void setExploratoryIspFeatureAck(bool enabled) noexcept {
    exploratoryIspFeatureAck = enabled;
}
void setExploratoryIspStatusZero(bool enabled) noexcept {
    exploratoryIspStatusZero = enabled;
}
void setExploratoryIspInitIdAck(bool enabled) noexcept {
    exploratoryIspInitIdAck = enabled;
}
void setExploratoryIspBusResetAck(bool enabled) noexcept {
    exploratoryIspBusResetAck = enabled;
}
void setExploratoryIspTarget0Ack(bool enabled) noexcept {
    exploratoryIspTarget0Ack = enabled;
}
void setExploratoryIspTargetSweep(bool enabled) noexcept {
    exploratoryIspTargetSweep = enabled;
}
uint32_t exploratoryIspMailboxCompletions() noexcept {
    return ispMailboxCompletions;
}
uint32_t exploratoryIspLoadedHighWater() noexcept {
    return exploratoryIspMailbox ? ispLoadedHighWater : 0;
}
uint32_t postExploratoryIspNoDeviceScanResponses() noexcept {
    if (!exploratoryIspMailbox || !ispBusResetAcknowledged ||
        ispNextTarget != 16 || ispRequestQueueEntries < 30 ||
        ispResponseQueueEntries < 15 || !physicalMemory)
        return 0;
    const auto localQueue = [](uint32_t bus, uint32_t entries) -> uint32_t {
        if (bus < 0xfe000000u || (bus & 15u) ||
            uint64_t{bus} + uint64_t{entries} * 64u > 0xff000000ull)
            return 0;
        return 0xc0000000u + bus - 0xfe000000u;
    };
    const uint32_t requests = localQueue(ispRequestQueueBus, 30);
    const uint32_t responses = localQueue(ispResponseQueueBus, 15);
    if (!requests || !responses) return 0;
    auto chip16 = [](uint32_t offset) -> ShortOrdinal& {
        return *reinterpret_cast<ShortOrdinal*>(physicalMemory.get() +
                                                 0x8bf00000u + offset);
    };
    if (chip16(0x78) != 30 || chip16(0x7a) != 0 ||
        chip16(0x0a) != 0 || chip16(0x0c) != 0)
        return 0;
    std::array<uint32_t, 15> handles{};
    const auto field16 = [](const uint8_t* entry, unsigned offset) {
        return uint16_t(entry[offset]) |
               (uint16_t(entry[offset + 1]) << 8);
    };
    for (unsigned i = 0; i < handles.size(); ++i) {
        const uint8_t* marker = physicalMemory.get() + requests + i * 128u;
        const uint8_t* command = marker + 64;
        const uint8_t target = i < 7 ? i : i + 1;
        if (marker[0] != 4 || marker[1] != 1 ||
            marker[8] != 0 || marker[9] != target || marker[10] != 1 ||
            command[0] != 9 || command[1] != 1 ||
            command[3] != 0 || command[8] != 0 ||
            command[9] != target || field16(command, 10) != 6 ||
            field16(command, 12) != 0x20 ||
            field16(command, 16) != 24 ||
            field16(command, 18) != 1 ||
            command[20] != 0x12 || command[21] != 0 ||
            command[22] != 0 || command[23] != 0 ||
            command[24] != 0x60 || command[25] != 0)
            return 0;
        std::memcpy(&handles[i], command + 4, sizeof(handles[i]));
        if (handles[i] < 0xc0000000u || handles[i] >= 0xc1000000u ||
            std::find(handles.begin(), handles.begin() + i, handles[i]) !=
                handles.begin() + i)
            return 0;
    }
    for (unsigned i = 0; i < handles.size(); ++i) {
        uint8_t* response = physicalMemory.get() + responses + i * 64u;
        std::memset(response, 0, 64);
        const uint32_t header = 0x00000103u;
        const uint32_t status = 0x00010000u; // INCOMPLETE hypothesis
        std::memcpy(response, &header, 4);
        std::memcpy(response + 4, &handles[i], 4);
        std::memcpy(response + 8, &status, 4);
    }
    chip16(0x7a) = 15;
    chip16(0x70) = 0x8020u;
    chip16(0x0a) = 4;
    chip16(0x0c) = 1;
    std::cout << "checkpoint isp-no-device-queue-probe requests=15 "
                 "responses=15 status=INCOMPLETE risc-executed=0\n"
              << std::flush;
    return 15;
}
bool readExploratoryIspRisc(uint32_t first, uint32_t count,
                            uint16_t* words) noexcept {
    if (!exploratoryIspMailbox || !words || !count || count > 64 ||
        first >= ispRiscRam.size() || first + count > ispRiscRam.size())
        return false;
    std::copy_n(ispRiscRam.begin() + first, count, words);
    return true;
}
void
Core::nonPortableBegin() noexcept {
    if (!physicalMemory) {
        // allocate 4 gigabytes of memory
        physicalMemory = std::make_unique<uint8_t[]>((0x1'0000'0000));
    }
    //if (!tagBits) {
    //    // tagBits are aligned to 32-bit boundaries
    //    tagBits = new bool[(0x1'0000'0000) >> 2]();
    //}


    // setup the
}



void
Core::lockBus() noexcept {
}

void
Core::unlockBus() noexcept {
}


bool
Core::runNonPortableSelfTests() noexcept {
    return true;
}

void
Core::assertFailureState() noexcept {
}

void
Core::deassertFailureState() noexcept {
}


namespace {
    constexpr uint8_t getOffset32(Address input) noexcept { return (input >> 2) & 0b11; }
    constexpr uint8_t getOffset16(Address input) noexcept { return (input >> 1) & 0b111; }
    constexpr uint8_t getOffset8(Address input) noexcept { return input & 0b1111; }
    constexpr uint8_t getOffset(Address input, TreatAsLongOrdinal) noexcept { return (input >> 3) & 0b1; }
    constexpr uint8_t getOffset(Address input, TreatAsOrdinal) noexcept { return getOffset32(input); }
    constexpr uint8_t getOffset(Address input, TreatAsInteger) noexcept { return getOffset32(input); }
    constexpr uint8_t getOffset(Address input, TreatAsShortOrdinal) noexcept { return getOffset16(input); }
    constexpr uint8_t getOffset(Address input, TreatAsShortInteger) noexcept { return getOffset16(input); }
    constexpr uint8_t getOffset(Address input, TreatAsByteOrdinal) noexcept { return getOffset8(input); }
    constexpr uint8_t getOffset(Address input, TreatAsByteInteger) noexcept { return getOffset8(input); }
    Cell&
    getCell(Address address) noexcept {
        return *reinterpret_cast<Cell*>(physicalMemory.get() + (address & 0xFFFF'FFF0));
    }
    template<typename T>
    T* getPointer(Address address) noexcept {
        return reinterpret_cast<T*>(physicalMemory.get() + address);
    }
    template<typename T>
    T& getMemoryReference(Address address) noexcept {
        return *(getPointer<T>(address));
    }
    template<typename T>
    T tryGetFromConsole() {
        auto value = static_cast<T>(std::cin.get());
        if (std::cin.fail()) {
            return static_cast<T>(-1);
        } else {
            return value;
        }
    }
    decltype(auto) getDurationSinceStartup() noexcept {
        return std::chrono::system_clock::now() - startup;
    }
    template<typename T>
    T micros() noexcept {
        return static_cast<T>(std::chrono::duration_cast<std::chrono::microseconds>(getDurationSinceStartup()).count());
    }
    template<typename T>
    T millis() noexcept {
        return static_cast<T>(std::chrono::duration_cast<std::chrono::milliseconds>(getDurationSinceStartup()).count());
    }
    template<typename T>
    T ioLoad(Address offset, TreatAs<T>) {
        DEBUG_LOG_LEVEL(1) {
            std::cout << __PRETTY_FUNCTION__ << "(0x" << std::hex << offset << ")" << std::endl;
        }
        if (auto target = offset & 0xFF'FFFF; target >= 0x10'0000) {
            return getMemoryReference<T>(offset);
        } else {
            switch (target) {
                case 0x00'0000:
                    return static_cast<T>(10 * 1024 * 1024);
                case 0x00'0004:
                    return static_cast<T>(20 * 1024 * 1024);
                case 0x00'0008:
                    return tryGetFromConsole<T>();
                case 0x00'0040:
                    return millis<T>();
                case 0x00'0044:
                    return micros<T>();
                default:
                    return 0;
            }
        }
    }
    template<typename T>
    void ioStore(Address offset, T value, TreatAs<T>) {
        DEBUG_LOG_LEVEL(1) {
            std::cout << __PRETTY_FUNCTION__ << "(0x" << std::hex << offset << ", 0x" << std::hex << static_cast<Ordinal>(value) << ")" << std::endl;
        }
        if (auto target = offset & 0xFF'FFFF; target >= 0x10'0000) {
            getMemoryReference<T>(offset) = value;
        } else {
            switch (target) {
                case 0x00'0008:
                    std::cout.put(static_cast<char>(value));
                    break;
                case 0x00'000C:
                    std::cout.flush();
                    break;
                default:
                    break;
            }
        }
    }
    template<typename T>
    T load(Address address, TreatAs<T>) {
        // AcceleRAID maps flash at 0xfef00000 and 80303 registers at 0xff... .
        // Treat registers as plain storage until their behavior is modeled.
        // The observed board has no live UART: the startup presence probe
        // writes 1 to 0xe0600007 but reads back 0.
        if (address == 0xe0600007) return static_cast<T>(0);
        if (hostDmaMailbox.valid &&
            address >= hostDmaMailbox.base &&
            uint64_t{address} + sizeof(T) <=
                uint64_t{hostDmaMailbox.base} + hostDmaMailbox.bytes.size()) {
            T result{};
            std::memcpy(&result, hostDmaMailbox.bytes.data() +
                        (address - hostDmaMailbox.base), sizeof(T));
            if (exploratoryMuDmaTrace && exploratoryMuHostReads++ < 32) {
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint mu-host-address-read address="
                          << std::setw(8) << address << " size=" << std::dec
                          << sizeof(T) << " backed=1\n" << std::flush;
            }
            return result;
        }
        if (hostDmaRingSlot.valid &&
            address >= hostDmaRingSlot.base &&
            uint64_t{address} + sizeof(T) <=
                uint64_t{hostDmaRingSlot.base} + hostDmaRingSlot.bytes.size()) {
            T result{};
            std::memcpy(&result, hostDmaRingSlot.bytes.data() +
                        (address - hostDmaRingSlot.base), sizeof(T));
            return result;
        }
        if constexpr (std::is_integral_v<T> && sizeof(T) <= 4) {
            const int dma_index = dmaStatusIndex(address);
            if (dma_index >= 0 && (address & 3u) + sizeof(T) <= 4)
                return static_cast<T>(dmaChannelStatus[dma_index] >>
                                      ((address & 3u) * 8u));
            if (exploratoryQlogicPci && (address & ~Address{3}) == 0x12a8 &&
                (address & 3u) + sizeof(T) <= 4)
                return static_cast<T>(secondaryPciSelector >> ((address & 3u) * 8u));
            if (exploratoryQlogicPci && (address & ~Address{3}) == 0x12b0 &&
                (address & 3u) + sizeof(T) <= 4)
                return static_cast<T>(secondaryPciData() >> ((address & 3u) * 8u));
            if (timer0Address(address & ~Address{3}) &&
                (address & 3u) + sizeof(T) <= 4)
                return static_cast<T>(timer0Word(address & ~Address{3}) >>
                                      ((address & 3u) * 8u));
            if (inboundMuAddress(address) && (address & 3u) + sizeof(T) <= 4) {
                const auto shift = (address & 3u) * 8u;
                return static_cast<T>(inboundMuWord(address) >> shift);
            }
        }
        auditRead(address);
        if (address == 0xe0400000 && exploratoryBoardSelector >= 0 &&
            !exploratoryBoardSelectorWritten)
            return static_cast<T>(exploratoryBoardSelector);
        return getMemoryReference<T>(address);
    }
    template<typename T>
    void store(Address address, T value, TreatAs<T>) {
        if (hostDmaRingSlot.valid &&
            address >= hostDmaRingSlot.base &&
            uint64_t{address} + sizeof(T) <=
                uint64_t{hostDmaRingSlot.base} + hostDmaRingSlot.bytes.size()) {
            std::memcpy(hostDmaRingSlot.bytes.data() +
                        (address - hostDmaRingSlot.base), &value, sizeof(T));
            return;
        }
        if constexpr (std::is_integral_v<T> && sizeof(T) <= 4) {
            const int dma_index = dmaStatusIndex(address);
            if (dma_index >= 0 && (address & 3u) + sizeof(T) <= 4) {
                // Intel 80303 CSR: bit 10 (Channel Active) is read-only;
                // sticky interrupt/error flags clear when written as one.
                // No DMA engine is implemented yet, so reset status is idle.
                dmaChannelStatus[dma_index] &= ~(
                    static_cast<Ordinal>(value) << ((address & 3u) * 8u));
                return;
            }
            if (exploratoryQlogicPci && (address & ~Address{3}) == 0x12a8 &&
                (address & 3u) + sizeof(T) <= 4) {
                const unsigned shift = (address & 3u) * 8u;
                const Ordinal mask = sizeof(T) == 4 ? 0xffffffffu :
                                     ((Ordinal{1} << (sizeof(T) * 8)) - 1u);
                secondaryPciSelector = (secondaryPciSelector & ~(mask << shift)) |
                                       ((static_cast<Ordinal>(value) & mask) << shift);
                return;
            }
            if (timer0Address(address & ~Address{3}) &&
                (address & 3u) + sizeof(T) <= 4) {
                const Address reg = address & ~Address{3};
                const unsigned shift = (address & 3u) * 8u;
                const Ordinal mask = sizeof(T) == 4 ? 0xffffffffu :
                                     ((Ordinal{1} << (sizeof(T) * 8)) - 1u);
                storeTimer0Word(reg, (timer0Word(reg) & ~(mask << shift)) |
                                     ((static_cast<Ordinal>(value) & mask) << shift));
                return;
            }
            if (inboundMuAddress(address) && (address & 3u) + sizeof(T) <= 4) {
                const auto shift = (address & 3u) * 8u;
                const Ordinal mask = sizeof(T) == 4 ? 0xffffffffu :
                                     ((Ordinal{1} << (sizeof(T) * 8)) - 1u);
                const Ordinal shifted = (static_cast<Ordinal>(value) & mask) << shift;
                const Address reg = address & ~Address{3};
                if (reg == 0x1320 || reg == 0x1324)
                    storeInboundMuWord(reg, shifted);
                else
                    storeInboundMuWord(reg, (inboundMuWord(reg) & ~(mask << shift)) |
                                            shifted);
                return;
            }
        }
        auditWrite(address, value);
        if (address == 0xe0400000) exploratoryBoardSelectorWritten = true;
        getMemoryReference<T>(address) = value;
        if constexpr (std::is_integral_v<T> && sizeof(T) <= 4) {
            if (exploratoryMuDmaTrace && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaOutput.valid && !hostDmaOutput.completed) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address >= 0xc0000000u &&
                    descriptor_address <= 0xc0ffffe0u &&
                    !(descriptor_address & 31u)) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    const Ordinal local = descriptor[3];
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostDmaOutput.base &&
                        descriptor[2] == 0 &&
                        local >= 0xc0000000u &&
                        local <= 0xc1000000u - hostDmaOutput.length &&
                        descriptor[4] == hostDmaOutput.length &&
                        descriptor[5] == 0x3fu) {
                        std::copy_n(physicalMemory.get() + local,
                                    hostDmaOutput.length,
                                    hostDmaOutput.bytes.begin());
                        hostDmaOutput.completed = true;
                        dmaChannelStatus[1] |= 1u << 8; // end of chain
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-host-copy descriptor="
                                  << std::setw(8) << descriptor_address
                                  << " local=" << std::setw(8) << local
                                  << " host=" << std::setw(8)
                                  << hostDmaOutput.base << " bytes=" << std::dec
                                  << hostDmaOutput.length << "\n"
                                  << std::flush;
                    }
                }
            }
            if (exploratoryMuDmaTrace && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaMailbox.valid && hostDmaMailbox.bytes[21] == 0x8e &&
                hostGuestOutput.valid && !hostGuestOutputDmaCompleted &&
                hostGuestOutput.length == 1004u) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address == 0xc0611320u) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostGuestOutput.base &&
                        descriptor[2] == 0 &&
                        descriptor[3] == 0xc060c300u &&
                        descriptor[4] == hostGuestOutput.length &&
                        descriptor[5] == 0x3fu) {
                        std::memcpy(physicalMemory.get() + hostGuestOutput.base,
                                    physicalMemory.get() + descriptor[3],
                                    hostGuestOutput.length);
                        hostGuestOutputDmaCompleted = true;
                        dmaChannelStatus[1] |= 1u << 8;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-ring-output descriptor="
                                  << std::setw(8) << descriptor_address
                                  << " local=" << std::setw(8) << descriptor[3]
                                  << " host=" << std::setw(8)
                                  << hostGuestOutput.base << " bytes=" << std::dec
                                  << hostGuestOutput.length << " eoc=1\n"
                                  << std::flush;
                    }
                }
            }
            if (exploratoryStockFollowupDma1 && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaMailbox.valid && hostDmaMailbox.bytes[21] == 0x8e &&
                hostGuestHealth.valid && !hostGuestHealthDmaCompleted &&
                hostGuestHealth.length == 128u) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address == 0xc0611320u) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostGuestHealth.base &&
                        descriptor[2] == 0 &&
                        descriptor[3] == 0xc060c300u &&
                        descriptor[4] == 128u &&
                        descriptor[5] == 0x3fu) {
                        std::memcpy(physicalMemory.get() + hostGuestHealth.base,
                                    physicalMemory.get() + descriptor[3], 128u);
                        hostGuestHealthDmaCompleted = true;
                        dmaChannelStatus[1] |= 1u << 8;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-ring-health descriptor="
                                  << std::setw(8) << descriptor_address
                                  << " local=" << std::setw(8) << descriptor[3]
                                  << " host=" << std::setw(8)
                                  << hostGuestHealth.base << " bytes=128 eoc=1\n"
                                  << std::flush;
                    }
                }
            }
            if (exploratoryStockFollowupDma1 && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaMailbox.valid && hostDmaMailbox.bytes[21] == 0x8e &&
                hostGuestPdev.valid && !hostGuestPdevDmaCompleted &&
                hostGuestPdev.length == 512u) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address == 0xc0611320u) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostGuestPdev.base &&
                        descriptor[2] == 0 &&
                        descriptor[3] == 0xc060c300u &&
                        descriptor[4] == 512u &&
                        descriptor[5] == 0x3fu) {
                        std::memcpy(physicalMemory.get() + hostGuestPdev.base,
                                    physicalMemory.get() + descriptor[3], 512u);
                        hostGuestPdevDmaCompleted = true;
                        dmaChannelStatus[1] |= 1u << 8;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-ring-pdev descriptor="
                                  << std::setw(8) << descriptor_address
                                  << " local=" << std::setw(8) << descriptor[3]
                                  << " host=" << std::setw(8)
                                  << hostGuestPdev.base << " bytes=512 eoc=1\n"
                                  << std::flush;
                    }
                }
            }
            if (exploratoryNativeRingDma1 && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaMailbox.valid && hostDmaMailbox.bytes[21] == 0x8e &&
                hostGuestOutput.valid && !hostGuestOutputDmaCompleted &&
                hostGuestOutput.length == 1004u) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address >= 0xc0000000u &&
                    descriptor_address <= 0xc0ffffe0u &&
                    !(descriptor_address & 31u)) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    const Ordinal local = descriptor[3];
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostGuestOutput.base &&
                        descriptor[2] == 0 &&
                        local >= 0xc0000000u &&
                        local <= 0xc1000000u - hostGuestOutput.length &&
                        descriptor[4] == hostGuestOutput.length &&
                        descriptor[5] == 0x3fu) {
                        std::memcpy(physicalMemory.get() + hostGuestOutput.base,
                                    physicalMemory.get() + local,
                                    hostGuestOutput.length);
                        hostGuestOutputDmaCompleted = true;
                        dmaChannelStatus[1] |= 1u << 8;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-native-ring-output "
                                  << "descriptor=" << std::setw(8)
                                  << descriptor_address << " local="
                                  << std::setw(8) << local << " host="
                                  << std::setw(8) << hostGuestOutput.base
                                  << " bytes=" << std::dec
                                  << hostGuestOutput.length << " eoc=1\n"
                                  << std::flush;
                    }
                }
            }
            if (exploratoryNativeRingHealthDma1 && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaMailbox.valid && hostDmaMailbox.bytes[21] == 0x8e &&
                hostGuestHealth.valid && !hostGuestHealthDmaCompleted &&
                hostGuestHealth.length == 128u) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address >= 0xc0000000u &&
                    descriptor_address <= 0xc0ffffe0u &&
                    !(descriptor_address & 31u)) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    const Ordinal local = descriptor[3];
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostGuestHealth.base &&
                        descriptor[2] == 0 &&
                        local >= 0xc0000000u &&
                        local <= 0xc1000000u - 128u &&
                        descriptor[4] == 128u &&
                        descriptor[5] == 0x3fu) {
                        std::memcpy(physicalMemory.get() + hostGuestHealth.base,
                                    physicalMemory.get() + local, 128u);
                        hostGuestHealthDmaCompleted = true;
                        dmaChannelStatus[1] |= 1u << 8;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-native-ring-health "
                                  << "descriptor=" << std::setw(8)
                                  << descriptor_address << " local="
                                  << std::setw(8) << local << " host="
                                  << std::setw(8) << hostGuestHealth.base
                                  << " bytes=128 eoc=1\n" << std::flush;
                    }
                }
            }
            if (exploratoryNativeRingPdevDma1 && address == 0x1440 &&
                sizeof(T) == 4 && (value & 1u) &&
                hostDmaMailbox.valid && hostDmaMailbox.bytes[21] == 0x8e &&
                hostGuestPdev.valid && !hostGuestPdevDmaCompleted &&
                hostGuestPdev.length == 512u) {
                Ordinal descriptor_address = 0;
                std::memcpy(&descriptor_address, physicalMemory.get() + 0x1450, 4);
                if (descriptor_address >= 0xc0000000u &&
                    descriptor_address <= 0xc0ffffe0u &&
                    !(descriptor_address & 31u)) {
                    std::array<Ordinal, 6> descriptor{};
                    std::memcpy(descriptor.data(),
                                physicalMemory.get() + descriptor_address,
                                sizeof(descriptor));
                    const Ordinal local = descriptor[3];
                    if (descriptor[0] == 0 &&
                        descriptor[1] == hostGuestPdev.base &&
                        descriptor[2] == 0 &&
                        local >= 0xc0000000u &&
                        local <= 0xc1000000u - 512u &&
                        descriptor[4] == 512u &&
                        descriptor[5] == 0x3fu) {
                        std::memcpy(physicalMemory.get() + hostGuestPdev.base,
                                    physicalMemory.get() + local, 512u);
                        hostGuestPdevDmaCompleted = true;
                        dmaChannelStatus[1] |= 1u << 8;
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint mu-dma1-native-ring-pdev "
                                  << "descriptor=" << std::setw(8)
                                  << descriptor_address << " local="
                                  << std::setw(8) << local << " host="
                                  << std::setw(8) << hostGuestPdev.base
                                  << " bytes=512 eoc=1\n" << std::flush;
                    }
                }
            }
            if (exploratoryMuDmaTrace && address >= 0x1400 &&
                address < 0x1480 && exploratoryMuDmaWrites++ < 96) {
                std::cout << std::hex << std::setfill('0')
                          << "checkpoint mu-primary-dma-write register="
                          << std::setw(4) << address << " size=" << std::dec
                          << sizeof(T) << " value=" << std::hex << std::setw(8)
                          << static_cast<uint32_t>(value) << "\n" << std::flush;
            }
        }
        if constexpr (std::is_integral_v<T> && sizeof(T) == 2) {
            // Narrow response hypothesis for the observed register test and
            // single-word RISC RAM operations. The ISP RISC is not executed.
            if (exploratoryIspMailbox && address == 0x8bf000c0u) {
                auto chip16 = [&](Address offset) -> ShortOrdinal& {
                    return *reinterpret_cast<ShortOrdinal*>(physicalMemory.get() +
                                                             0x8bf00000u + offset);
                };
                if (value == 0x5000u) {
                    const ShortOrdinal command = chip16(0x70);
                    bool completed = false;
                    if (command == 0x0004u) {
                        ispRiscRam[chip16(0x72)] = chip16(0x74);
                        ispExecuteAcknowledged = false;
                        ispAboutAcknowledged = false;
                    } else if (command == 0x0005u)
                        chip16(0x74) = ispRiscRam[chip16(0x72)];
                    if (command == 0x0004u || command == 0x0005u ||
                        command == 0x0006u)
                        completed = true;
                    if (command == 0x0007u &&
                        ispLoadedHighWater > chip16(0x72)) {
                        uint32_t checksum = 0;
                        for (uint32_t i = chip16(0x72);
                             i < ispLoadedHighWater; ++i)
                            checksum += ispRiscRam[i];
                        completed = (checksum & 0xffffu) == 0;
                    }
                    if (command == 0x0002u && exploratoryIspExecuteAck &&
                        chip16(0x72) == 0x1000u &&
                        ispLoadedHighWater == 0x4379u &&
                        ispRiscRam[0x1000] == 0x0804u &&
                        ispRiscRam[0x1001] == 0x1041u &&
                        ispRiscRam[0x1003] == 0x3379u &&
                        ispRiscRam[0x1005] == 0x2043u) {
                        uint32_t checksum = 0;
                        uint64_t fingerprint = 0xcbf29ce484222325ull;
                        for (uint32_t i = 0x1000; i < 0x4379; ++i) {
                            checksum += ispRiscRam[i];
                            for (unsigned shift : {0u, 8u}) {
                                fingerprint ^= (ispRiscRam[i] >> shift) & 0xffu;
                                fingerprint *= 0x100000001b3ull;
                            }
                        }
                        // FNV-1a over the 26,354 bytes captured from stock.
                        // This is a probe guard, not firmware authentication.
                        completed = (checksum & 0xffffu) == 0 &&
                                    fingerprint == 0x4a609c51ff728b7dull;
                        if (completed) {
                            ispExecuteAcknowledged = true;
                            ispAboutAcknowledged = false;
                            std::cout << "checkpoint isp-execute-ack-stub "
                                         "image=isp1216-10.01 "
                                         "firmware-executed=0\n" << std::flush;
                        }
                    }
                    if (command == 0x0008u && exploratoryIspAboutAck &&
                        ispExecuteAcknowledged) {
                        // The published QLogic host driver reads major and
                        // minor from MB1/MB2. These values come from the
                        // captured image's packed version string, not ISP
                        // instruction execution.
                        chip16(0x72) = 10;
                        chip16(0x74) = 1;
                        chip16(0x76) = 0;
                        completed = true;
                        ispAboutAcknowledged = true;
                        std::cout << "checkpoint isp-about-ack-stub "
                                     "version=10.01 firmware-executed=0\n"
                                  << std::flush;
                    }
                    if ((command == 0x0010u || command == 0x0011u) &&
                        exploratoryIspQueueAck && ispAboutAcknowledged) {
                        const uint32_t entries = chip16(0x72);
                        const uint32_t bus =
                            (uint32_t{chip16(0x74)} << 16) | chip16(0x76);
                        const uint64_t end = uint64_t{bus} + entries * 64ull;
                        const bool prior_queue = command == 0x0010u ||
                                                 ispRequestQueueEntries != 0;
                        const bool empty_index = chip16(command == 0x0010u ?
                                                         0x78 : 0x7au) == 0;
                        if (prior_queue && empty_index && entries &&
                            entries <= 1024u && (bus & 15u) == 0 &&
                            bus >= 0xfe000000u && end <= 0xff000000ull) {
                            if (command == 0x0010u) {
                                ispRequestQueueBus = bus;
                                ispRequestQueueEntries = entries;
                            } else {
                                ispResponseQueueBus = bus;
                                ispResponseQueueEntries = entries;
                            }
                            completed = true;
                            std::cout << std::hex << std::setfill('0')
                                      << "checkpoint isp-queue-ack-stub kind="
                                      << (command == 0x0010u ? "request" : "response")
                                      << " bus=" << std::setw(8) << bus
                                      << " entries=" << entries
                                      << " firmware-executed=0 iocbs-processed=0\n"
                                      << std::flush;
                        }
                    }
                    if (command == 0x0032u && exploratoryIspRetryAck &&
                        ispExecuteAcknowledged && ispAboutAcknowledged &&
                        ispRequestQueueEntries && ispResponseQueueEntries &&
                        chip16(0x72) == 0 && chip16(0x74) == 2 &&
                        chip16(0x76) == 0 && chip16(0x78) == 0 &&
                        chip16(0x7a) == 0) {
                        completed = true;
                        ispRetryAcknowledged = true;
                        std::cout << "checkpoint isp-retry-ack-stub "
                                     "retry=0 delay=2 firmware-executed=0 "
                                     "iocbs-processed=0\n" << std::flush;
                    }
                    if (command == 0x003au && exploratoryIspResetDelayAck &&
                        ispRetryAcknowledged &&
                        chip16(0x72) == 1 && chip16(0x74) == 1 &&
                        chip16(0x76) == 0 && chip16(0x78) == 0 &&
                        chip16(0x7a) == 0) {
                        completed = true;
                        ispResetDelayAcknowledged = true;
                        std::cout << "checkpoint isp-reset-delay-ack-stub "
                                     "mb1=1 mb2=1 firmware-executed=0 "
                                     "iocbs-processed=0\n" << std::flush;
                    }
                    if (command == 0x0035u && exploratoryIspActiveNegationAck &&
                        ispResetDelayAcknowledged &&
                        chip16(0x72) == 0x30 && chip16(0x74) == 0x30 &&
                        chip16(0x76) == 0 && chip16(0x78) == 0 &&
                        chip16(0x7a) == 0) {
                        completed = true;
                        ispActiveNegationAcknowledged = true;
                        std::cout << "checkpoint isp-active-negation-ack-stub "
                                     "mb1=30 mb2=30 firmware-executed=0 "
                                     "iocbs-processed=0\n" << std::flush;
                    }
                    if (command == 0x004au && exploratoryIspFeatureAck &&
                        ispActiveNegationAcknowledged &&
                        chip16(0x72) == 0x16 && chip16(0x74) == 0x30 &&
                        chip16(0x76) == 0 && chip16(0x78) == 0 &&
                        chip16(0x7a) == 0) {
                        completed = true;
                        ispFeatureAcknowledged = true;
                        std::cout << "checkpoint isp-feature-ack-stub "
                                     "mb1=16 mb2=30 semantics=unknown "
                                     "firmware-executed=0 iocbs-processed=0\n"
                                  << std::flush;
                    }
                    if (command == 0x001fu && exploratoryIspStatusZero &&
                        ispFeatureAcknowledged &&
                        chip16(0x72) == 0x16 && chip16(0x74) == 0x30 &&
                        chip16(0x76) == 0 && chip16(0x78) == 0 &&
                        chip16(0x7a) == 0) {
                        // MB1/MB2 are outputs for this command. Zero is an
                        // explicit experiment, not a measured ISP result.
                        chip16(0x72) = 0;
                        chip16(0x74) = 0;
                        completed = true;
                        ispStatusZeroAcknowledged = true;
                        std::cout << "checkpoint isp-status-zero-hypothesis "
                                     "mb1=0 mb2=0 measured=0 "
                                     "firmware-executed=0 iocbs-processed=0\n"
                                  << std::flush;
                    }
                    if (command == 0x0030u && exploratoryIspInitIdAck &&
                        ispStatusZeroAcknowledged && chip16(0x72) == 7 &&
                        chip16(0x74) == 0 && chip16(0x76) == 0 &&
                        chip16(0x78) == 0 && chip16(0x7a) == 0) {
                        completed = true;
                        ispInitIdAcknowledged = true;
                        std::cout << "checkpoint isp-init-id-ack-stub "
                                     "id=7 firmware-executed=0 "
                                     "iocbs-processed=0\n" << std::flush;
                    }
                    if (command == 0x0018u && exploratoryIspBusResetAck &&
                        ispInitIdAcknowledged && chip16(0x72) == 1 &&
                        chip16(0x74) == 0 && chip16(0x76) == 0 &&
                        chip16(0x78) == 0 && chip16(0x7a) == 0) {
                        completed = true;
                        ispBusResetAcknowledged = true;
                        std::cout << "checkpoint isp-bus-reset-ack-stub "
                                     "bus=1 scsi-reset=0 firmware-executed=0 "
                                     "iocbs-processed=0\n" << std::flush;
                    }
                    if (command == 0x0038u && exploratoryIspTarget0Ack &&
                        ispBusResetAcknowledged && ispNextTarget == 0 &&
                        chip16(0x72) == 0 &&
                        chip16(0x74) == 0xc500 && chip16(0x76) == 0x0c0c &&
                        chip16(0x78) == 0 && chip16(0x7a) == 0) {
                        completed = true;
                        ispNextTarget = 1;
                        std::cout << "checkpoint isp-target0-ack-stub "
                                     "mb1=0 mb2=c500 mb3=0c0c "
                                     "firmware-executed=0 iocbs-processed=0\n"
                                  << std::flush;
                    }
                    if (command == 0x0038u && exploratoryIspTargetSweep &&
                        ispBusResetAcknowledged && ispNextTarget >= 1 &&
                        ispNextTarget < 16 &&
                        chip16(0x72) == ispNextTarget << 8 &&
                        chip16(0x74) == 0xc500 && chip16(0x76) == 0x0c0c &&
                        chip16(0x78) == 0 && chip16(0x7a) == 0) {
                        completed = true;
                        std::cout << "checkpoint isp-target-sweep-ack-stub "
                                     "target=" << ispNextTarget
                                  << " firmware-executed=0 iocbs-processed=0\n"
                                  << std::flush;
                        ++ispNextTarget;
                    }
                    if (command == 0x0001u || command == 0x0003u ||
                        command == 0x0009u || command == 0x000au) {
                        // In the installed runtime's DMA test, c00829d0
                        // translates c0600df0 to fe600df0. The 16 MiB
                        // aperture assumption is bounded and opt-in.
                        const uint32_t bus =
                            (uint32_t{chip16(0x74)} << 16) | chip16(0x76);
                        const uint32_t count = chip16(0x78);
                        const uint32_t risc = chip16(0x72);
                        if (count && risc + count <= ispRiscRam.size() &&
                            bus >= 0xfe000000u &&
                            uint64_t{bus} + count * 2u <= 0xff000000ull) {
                            const Address local = 0xc0000000u +
                                                  (bus - 0xfe000000u);
                            for (uint32_t i = 0; i < count; ++i) {
                                ShortOrdinal word;
                                if (command == 0x0001u || command == 0x0009u) {
                                    std::memcpy(&word, physicalMemory.get() +
                                                       local + i * 2u, 2);
                                    ispRiscRam[risc + i] = word;
                                } else {
                                    word = ispRiscRam[risc + i];
                                    std::memcpy(physicalMemory.get() + local +
                                                i * 2u, &word, 2);
                                }
                            }
                            if (command == 0x0001u)
                                ispLoadedHighWater = std::max(ispLoadedHighWater,
                                                              risc + count);
                            if (command == 0x0001u || command == 0x0009u)
                                ispExecuteAcknowledged = false;
                            if (command == 0x0001u || command == 0x0009u)
                                ispAboutAcknowledged = false;
                            completed = true;
                        }
                    }
                    if (completed) {
                        chip16(0x70) = 0x4000u;
                        chip16(0x0a) = 0x0006u;
                        chip16(0x0c) = 0x0003u; // lock+status until ack
                        ++ispMailboxCompletions;
                    } else if (!ispUnknownCommandTraced) {
                        ispUnknownCommandTraced = true;
                        uint32_t checksum = 0;
                        for (uint32_t i = chip16(0x72);
                             i < ispRiscRam.size(); ++i)
                            checksum += ispRiscRam[i];
                        uint32_t loaded_checksum = 0;
                        for (uint32_t i = chip16(0x72);
                             i < ispLoadedHighWater; ++i)
                            loaded_checksum += ispRiscRam[i];
                        std::cout << std::hex << std::setfill('0')
                                  << "checkpoint isp-unmodeled-command opcode="
                                  << command << " mb1=" << chip16(0x72)
                                  << " mb2=" << chip16(0x74)
                                  << " mb3=" << chip16(0x76)
                                  << " mb4=" << chip16(0x78)
                                  << " mb5=" << chip16(0x7a)
                                  << " risc-sum16=" << (checksum & 0xffffu)
                                  << " loaded-end=" << ispLoadedHighWater
                                  << " loaded-sum16=" << (loaded_checksum & 0xffffu)
                                  << "\n"
                                  << std::flush;
                    }
                } else if (value == 0x1000u) {
                    ispExecuteAcknowledged = false;
                    ispAboutAcknowledged = false;
                    ispRequestQueueBus = 0;
                    ispRequestQueueEntries = 0;
                    ispResponseQueueBus = 0;
                    ispResponseQueueEntries = 0;
                    ispRetryAcknowledged = false;
                    ispResetDelayAcknowledged = false;
                    ispActiveNegationAcknowledged = false;
                    ispFeatureAcknowledged = false;
                    ispStatusZeroAcknowledged = false;
                } else if (value == 0x7000u) {
                    chip16(0x0a) = 0;
                    chip16(0x0c) = 0;
                }
                if (ispHccrTraces++ < 16)
                    std::cout << std::hex << std::setfill('0')
                              << "checkpoint isp-hccr command=" << value
                              << " mailbox0=" << chip16(0x70)
                              << " isr=" << chip16(0x0a)
                              << " semaphore=" << chip16(0x0c) << "\n"
                              << std::flush;
                chip16(0xc0) = 0; // command register reads as status
            }
        }
    }
    void
    store8(Address address, ByteOrdinal value, TreatAsByteOrdinal) noexcept {
        store(address, value, TreatAsByteOrdinal{});
    }
    void Cell::setValue(Address address, ByteOrdinal value, TreatAsByteOrdinal) noexcept { bytes[getOffset(address, TreatAsByteOrdinal{})] = value; }
    void Cell::setValue(Address address, ByteInteger value, TreatAsByteInteger) noexcept { byteIntegers[getOffset(address, TreatAsByteInteger{})] = value; }
    void Cell::setValue(Address address, ShortOrdinal value, TreatAsShortOrdinal) noexcept { shortOrdinals[getOffset(address, TreatAsShortOrdinal{})] = value; }
    void Cell::setValue(Address address, ShortInteger value, TreatAsShortInteger) noexcept { shortIntegers[getOffset(address, TreatAsShortInteger{})] = value; }
    void Cell::setValue(Address address, Ordinal value, TreatAsOrdinal) noexcept { ordinals[getOffset(address, TreatAsOrdinal{})] = value; }
    void Cell::setValue(Address address, Integer value, TreatAsInteger) noexcept { integers[getOffset(address, TreatAsInteger{})] = value; }
    void Cell::setValue(Address address, LongOrdinal value, TreatAsLongOrdinal) noexcept { longOrdinals[getOffset(address, TreatAsLongOrdinal{})] = value; }
    ByteOrdinal
    Cell::getValue(Address address, TreatAsByteOrdinal) const noexcept {
        return bytes[getOffset(address, TreatAsByteOrdinal{})];
    }

    ByteInteger
    Cell::getValue(Address address, TreatAsByteInteger) const noexcept {
        return byteIntegers[getOffset(address, TreatAsByteInteger{})];
    }

    ShortOrdinal
    Cell::getValue(Address address, TreatAsShortOrdinal) const noexcept {
        return shortOrdinals[getOffset(address, TreatAsShortOrdinal{})];
    }

    ShortInteger
    Cell::getValue(Address address, TreatAsShortInteger) const noexcept {
        return shortIntegers[getOffset(address, TreatAsShortInteger{})];

    }
    Ordinal
    Cell::getValue(Address address, TreatAsOrdinal) const noexcept {
        return ordinals[getOffset(address, TreatAsOrdinal{})];
    }

    Integer
    Cell::getValue(Address address, TreatAsInteger) const noexcept {
        return integers[getOffset(address, TreatAsInteger{})];
    }

    LongOrdinal
    Cell::getValue(Address address, TreatAsLongOrdinal) const noexcept {
        return longOrdinals[getOffset(address, TreatAsLongOrdinal{})];
    }

}

Ordinal
Core::load(Address address, TreatAsOrdinal) const noexcept {
    return ::load(address, TreatAsOrdinal{});
}

Integer
Core::load(Address address, TreatAsInteger) const noexcept {
    return ::load(address, TreatAsInteger{});
}



void
Core::store(Address address, Ordinal value, TreatAsOrdinal) noexcept {
    ::store(address, value, TreatAsOrdinal{});
}

void
Core::store(Address address, Integer value, TreatAsInteger) noexcept {
    ::store(address, value, TreatAsInteger{});
}

void
Core::store(Address address, ShortOrdinal value, TreatAsShortOrdinal) noexcept {
    ::store(address, value, TreatAsShortOrdinal{});
}

void
Core::store(Address address, ShortInteger value, TreatAsShortInteger) noexcept {
    ::store(address, value, TreatAsShortInteger{});
}

void
Core::store(Address address, ByteOrdinal value, TreatAsByteOrdinal) noexcept {
    ::store(address, value, TreatAsByteOrdinal {});
}

void
Core::store(Address address, ByteInteger value, TreatAsByteInteger) noexcept {
    ::store(address, value, TreatAsByteInteger{});
}
void
Core::checksumFail() {
    throw std::runtime_error("checksum fail");
    // cause termination to happen
}
void
Core::selfTestFailure() {
    throw std::runtime_error("self test failure!");
}
void
Core::badFault(const FaultRecord& record) {
    throw std::runtime_error("bad fault");
}

void
installToMainMemory(std::istream& stream, Address baseAddress) {
    while (stream.good()) {
        store8(baseAddress, stream.get(), TreatAsByteOrdinal {});
        ++baseAddress;
    }
}
void
installToMainMemory(Address baseAddress, const char* data, Address size) {
    for (auto addr = 0; addr < size; ++addr) {
        store8(baseAddress + addr, data[addr], TreatAsByteOrdinal{});
    }
}
void
clearMainMemory(Address baseAddress, Address size) {
    for (auto addr = 0; addr < size; ++addr) {
        store8(baseAddress + addr, 0, TreatAsByteOrdinal{});
    }
}
namespace {
    void
    Cell::setValue(Address, QuadOrdinal value, TreatAs<QuadOrdinal>) noexcept {
        // only works on aligned values so don't check address
        quadOrdinal = value;
    }
    QuadOrdinal Cell::getValue(Address, TreatAs<QuadOrdinal>) const noexcept { return quadOrdinal; }
}
void
Core::store(Address address, QuadOrdinal value, TreatAsQuadOrdinal) noexcept {
    ::store(address, value, TreatAsQuadOrdinal {});
}

QuadOrdinal
Core::load(Address address, TreatAsQuadOrdinal) const noexcept {
    return ::load(address, TreatAsQuadOrdinal{});
}

LongOrdinal
Core::load(Address address, TreatAs<LongOrdinal>) const noexcept {
    return ::load(address, TreatAsLongOrdinal{});
}

void
Core::store(Address address, LongOrdinal value, TreatAs<LongOrdinal>) noexcept {
    ::store(address, value, TreatAsLongOrdinal{});
}
