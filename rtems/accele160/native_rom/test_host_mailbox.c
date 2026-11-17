/* Validate the parser against the QEMU-captured request and bad DMA inputs. */
#include "host_mailbox.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void rejects(const unsigned char *original, unsigned int offset,
                    unsigned char value, unsigned int reason)
{
    unsigned char changed[64];
    accele160_controller_info_request out = { 0xfeedu, 0xbeefu, 0xfaceu };
    memcpy(changed, original, sizeof(changed));
    changed[offset] = value;
    assert(accele160_parse_controller_info(changed, 64, &out) == reason);
    assert(out.command_id == 0xfeedu && out.output_bus_address == 0xbeefu &&
           out.output_bytes == 0xfaceu);
}

int main(int argc, char **argv)
{
    FILE *input;
    unsigned char mailbox[64];
    accele160_controller_info_request out;
    assert(argc == 2);
    input = fopen(argv[1], "rb");
    assert(input);
    assert(fread(mailbox, 1, sizeof(mailbox), input) == sizeof(mailbox));
    assert(fgetc(input) == EOF);
    assert(fclose(input) == 0);
    assert(accele160_parse_controller_info(mailbox, 64, &out) ==
           ACCELE160_MAILBOX_OK);
    assert(out.command_id == 0x7fu && out.output_bus_address == 0x9f3e0u &&
           out.output_bytes == 512u);
    rejects(mailbox, 2, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(mailbox, 3, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(mailbox, 5, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(mailbox, 21, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(mailbox, 41, 0, ACCELE160_MAILBOX_UNSUPPORTED);
    rejects(mailbox, 32, 1, ACCELE160_MAILBOX_ADDRESS);
    rejects(mailbox, 36, 1, ACCELE160_MAILBOX_ADDRESS);
    {
        unsigned char changed[64];
        memcpy(changed, mailbox, sizeof(changed));
        memset(changed + 32, 0, 4);
        assert(accele160_parse_controller_info(changed, 64, &out) ==
               ACCELE160_MAILBOX_ADDRESS);
        memset(changed + 32, 0xff, 4);
        assert(accele160_parse_controller_info(changed, 64, &out) ==
               ACCELE160_MAILBOX_ADDRESS);
    }
    assert(accele160_parse_controller_info(mailbox, 63, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_controller_info(0, 64, &out) ==
           ACCELE160_MAILBOX_SHORT);
    assert(accele160_parse_controller_info(mailbox, 64, 0) ==
           ACCELE160_MAILBOX_SHORT);
    puts("GET_CTLR_INFO mailbox parser PASS");
    return 0;
}
