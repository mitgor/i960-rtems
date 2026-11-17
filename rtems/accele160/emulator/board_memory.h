#pragma once
#include <cstdint>

struct BoardMemoryAudit {
    bool unknown_read = false;
    bool unknown_write = false;
    uint32_t first_read = 0;
    uint32_t first_write = 0;
};

// Exploratory memory backend audit. Unknown peripheral accesses still return
// or store zero-backed bytes; callers must not treat a resulting trace as a
// validated board boot.
void resetBoardMemoryAudit() noexcept;
BoardMemoryAudit getBoardMemoryAudit() noexcept;
void setExploratoryBoardSelector(int value) noexcept;

// 80303 primary-PCI configuration retry (Intel 273395-005 mode 3; register
// layout in developer's manual 273353-001, table 14-46). With the
// RETRY pin strapped high the bridge answers every host configuration cycle
// with Retry until the i960 clears EBCR (local 0x1040) bit 2. The model is
// opt-in because this board's strap is inferred from stock firmware (it
// writes EBCR=0x48 and then prints "BIOS Cfg Wait..."), not measured.
struct ConfigRetryState {
    bool modeled = false;
    bool released = false;        // meaningful only when modeled
    uint16_t ebcr = 0;
    uint64_t release_cycle = 0;   // cycle of the first releasing write
    uint32_t release_ip = 0;
    uint32_t register_writes = 0; // traced stores, any origin
};
// Call after the core reset. A high RETRY strap starts at EBCR=0x000c;
// a low strap starts at 0x0008 with configuration cycles already accepted.
void applyExploratoryConfigRetryStrap(bool enabled, bool retry_pin_high = true) noexcept;
ConfigRetryState exploratoryConfigRetryState() noexcept;
// Log every store into the host-facing register blocks (bridge 0x1000..0x10ff,
// ATU 0x1200..0x12ff, messaging unit 0x1300..0x13ff) as "checkpoint
// pci-reg-write ...". Values are what firmware wrote; read-modify-write
// results depend on modeled (zero) reset values.
void setExploratoryPciRegisterTrace(bool enabled) noexcept;
void noteExploratoryTraceCycle(uint64_t cycle, uint32_t ip) noexcept;
// Mark stores issued on behalf of the host through the diagnostic bridge.
void setExploratoryPciWriteFromHost(bool host) noexcept;
// Opt-in secondary PCI configuration readback for the physically captured
// channel-0 QLogic ISP10160. Writes only select SOCCAR; no chip behavior.
void setExploratoryQlogicPci(bool enabled) noexcept;
// Hypothetical ISP10160 register test, word RAM and bounded DMA test commands
// used only by an explicit offline experiment. No QLogic firmware is executed.
void setExploratoryIspMailbox(bool enabled) noexcept;
// Host-flow probe only: acknowledge EXEC FIRMWARE for the captured, checksum-
// valid ISP1216 image. Does not run an ISP instruction.
void setExploratoryIspExecuteAck(bool enabled) noexcept;
// Protocol-only ABOUT FIRMWARE response using the captured 10.01 image text.
void setExploratoryIspAboutAck(bool enabled) noexcept;
// Protocol-only queue registration; validates the bounded DMA ring and stores
// its base/count, but does not fetch or execute IOCBs.
void setExploratoryIspQueueAck(bool enabled) noexcept;
// Protocol-only response to the observed SET RETRY COUNT (0, 2) command,
// after both bounded queues were registered. Does not execute ISP firmware.
void setExploratoryIspRetryAck(bool enabled) noexcept;
// Protocol-only response to the observed SET RESET DELAY PARAMS (1, 1)
// after the retry and queue setup probes. No ISP instruction runs.
void setExploratoryIspResetDelayAck(bool enabled) noexcept;
// Protocol-only response to the observed SET ACTIVE NEGATION (0x30, 0x30)
// after reset-delay setup. Does not model SCSI signalling.
void setExploratoryIspActiveNegationAck(bool enabled) noexcept;
// Trace-only acknowledgment of the exact observed SET FW FEATURES request.
// The meaning of feature bit 0x10 is not established for this ISP firmware.
void setExploratoryIspFeatureAck(bool enabled) noexcept;
// Diagnostic hypothesis only: fabricated zero firmware-status data.
void setExploratoryIspStatusZero(bool enabled) noexcept;
void setExploratoryIspInitIdAck(bool enabled) noexcept;
// Protocol-only acknowledgment of the observed BUS RESET (bus 1) after
// initiator-ID setup. No SCSI electrical reset or ISP code is executed.
void setExploratoryIspBusResetAck(bool enabled) noexcept;
// Accept only the first observed SET TARGET PARAMETERS request so the next
// firmware request can be identified; target scan behavior remains unmodeled.
void setExploratoryIspTarget0Ack(bool enabled) noexcept;
// Explore only an ordered 1..15 target parameter sweep after target 0.
void setExploratoryIspTargetSweep(bool enabled) noexcept;
uint32_t exploratoryIspMailboxCompletions() noexcept;
uint32_t exploratoryIspLoadedHighWater() noexcept;
// Explicit offline hypothesis: validate the observed 15 paired INQUIRY
// IOCBs, then post 15 INCOMPLETE/no-device status entries to the registered
// response queue. Returns 15 only on an exact guarded match; executes no
// ISP RISC instructions and performs no SCSI bus transaction.
uint32_t postExploratoryIspNoDeviceScanResponses() noexcept;
bool readExploratoryIspRisc(uint32_t first, uint32_t count,
                            uint16_t* words) noexcept;

// Minimal 80303 inbound MU model. Host writes latch the two message words and
// set doorbell bit 0; the i960 clears the doorbell by writing that bit back.
void resetInboundMu() noexcept;
bool submitInboundMailbox(uint64_t dma_address) noexcept;
// The coupled QEMU probe supplies 64 host-memory bytes with the MU pointer.
// This bounded staging area is readable by a future host-DMA model.
bool submitInboundMailboxPayload(uint64_t dma_address,
                                 const uint8_t* bytes, uint32_t length) noexcept;
// Exploratory memory-mailbox window: stage only the first 64-byte guest ring
// slot at its exact DMA address. No ring status or DMA completion is generated.
bool stageExploratoryHostRingSlot(uint64_t dma_address,
                                  const uint8_t* bytes, uint32_t length) noexcept;
bool registerExploratoryHostGuestWindow(char kind, uint64_t dma_address,
                                         uint32_t length) noexcept;
bool exploratoryHostGuestWindowContains(uint64_t dma_address,
                                        uint32_t length) noexcept;
bool readExploratoryHostDma(uint64_t address, uint8_t* bytes,
                            uint32_t length) noexcept;
bool readExploratoryHostDmaOutput(uint64_t address, uint8_t* bytes,
                                  uint32_t length) noexcept;
void acknowledgeExploratoryOutboundDoorbell(uint32_t bits) noexcept;
uint32_t exploratoryHostDmaBase() noexcept;
// Diagnostic only: log the bounded primary DMA register writes after a
// forced MU vector. This does not perform transfers or deliver interrupts.
void enableExploratoryMuDmaTrace() noexcept;
// Opt-in native first-ring DMA1 transfer into the registered model window.
void enableExploratoryNativeRingDma1() noexcept;
void enableExploratoryNativeRingHealthDma1() noexcept;
void enableExploratoryNativeRingPdevDma1() noexcept;
void enableExploratoryStockFollowupDma1() noexcept;
// Test-only host input for tracing firmware readiness paths; no PCI source yet.
void postExploratoryInboundDoorbell(uint32_t bits) noexcept;
// Raw inbound MU interrupt request after IIMR masking. This does not route an
// XINT line or enter the i960 interrupt handler.
uint32_t inboundMuUnmaskedStatus() noexcept;

// Exploratory clock: one modeled 80303 bus clock per executed instruction.
// Timer 0 latches its TINT0 pending bit in the core IPND register; CPU
// interrupt entry and real instruction/bus-clock ratios remain unmodeled.
void resetExploratoryTimer0() noexcept;
void advanceExploratoryBusClock() noexcept;
uint64_t exploratoryTimer0Events() noexcept;

