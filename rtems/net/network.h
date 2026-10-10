void network_init(void);
void network_step(unsigned int ms,const unsigned char *packet,unsigned int length);
unsigned int network_output(unsigned char *out,unsigned int capacity);
void network_fetch(const char *name,unsigned int port);
unsigned int network_report(unsigned char *out);
unsigned int network_fetch_data(unsigned char *out,unsigned int offset,unsigned int limit);
