#include <assert.h>
#include <stdio.h>
#include "graph.h"
int main(void){struct dep_graph g;unsigned int w[9],out[9],i,rc;
 graph_reset(&g);assert(!graph_claim(&g,0,0));assert(!graph_claim(&g,1,1));assert(!graph_wait(&g,1,0));assert(!graph_wait(&g,2,1));assert(graph_closure(&g,1)==7);assert(graph_wait(&g,0,1)==G_CYCLE);assert(graph_freeze(&g,1)==7);assert(graph_wait(&g,0,1)==G_CLOSED);
 assert(graph_release(&g,2,0)==G_STATE);assert(!graph_release(&g,0,0));assert(!graph_claim(&g,1,0));assert(!graph_release(&g,1,0));assert(!graph_release(&g,1,1));assert(!graph_claim(&g,2,1));assert(!graph_release(&g,2,1));assert(graph_claim(&g,0,0)==G_CLOSED);assert(!graph_claim(&g,3,0));
 while(fread(w,sizeof(w),1,stdin)==1){for(i=0;i<2;i++)g.owner[i]=w[i];for(i=0;i<4;i++)g.wait[i]=w[2+i];g.closed=w[6];out[0]=graph_closure(&g,1u<<w[7]);rc=graph_wait(&g,w[7],w[8]);out[1]=rc;for(i=0;i<2;i++)out[2+i]=g.owner[i];for(i=0;i<4;i++)out[4+i]=g.wait[i];out[8]=g.closed;if(fwrite(out,sizeof(out),1,stdout)!=1)return 1;}
 return 0;
}
