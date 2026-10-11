/* Four tasks, two resources, bounded transitive dependency closure. */
#ifndef PIRQ_GRAPH_H
#define PIRQ_GRAPH_H
#define G_NONE 4u
#define G_OK 0u
#define G_STATE 3u
#define G_CYCLE 4u
#define G_CLOSED 5u
struct dep_graph {unsigned int owner[2],wait[4],closed;};
static void graph_reset(struct dep_graph*g){unsigned int i;for(i=0;i<2;i++)g->owner[i]=G_NONE;for(i=0;i<4;i++)g->wait[i]=0;g->closed=0;}
static unsigned int graph_closure(const struct dep_graph*g,unsigned int seed){unsigned int i,n,r,mask=seed&15;
 for(n=0;n<4;n++)for(i=0;i<4;i++)if(g->wait[i]){r=g->wait[i]-1;if(r<2&&g->owner[r]<4&&(mask&(1u<<g->owner[r])))mask|=1u<<i;}
 return mask;
}
static unsigned int graph_wait(struct dep_graph*g,unsigned int task,unsigned int r){
 if(task>=4||r>=2||g->wait[task]||g->owner[r]==task)return G_STATE;
 if(g->closed&(1u<<task))return G_CLOSED;
 if(g->owner[r]<4&&(graph_closure(g,1u<<task)&(1u<<g->owner[r])))return G_CYCLE;
 g->wait[task]=r+1;return 0;
}
static unsigned int graph_claim(struct dep_graph*g,unsigned int task,unsigned int r){
 if(task>=4||r>=2||g->owner[r]!=G_NONE)return G_STATE;
 /* A pending admitted waiter can complete a handoff after admission closes. */
 if(g->wait[task]!=r+1&&(g->closed&(1u<<task)))return G_CLOSED;
 if(g->wait[task]&&g->wait[task]!=r+1)return G_STATE;
 g->owner[r]=task;g->wait[task]=0;return 0;
}
static unsigned int graph_release(struct dep_graph*g,unsigned int task,unsigned int r){
 if(task>=4||r>=2||g->owner[r]!=task)return G_STATE;g->owner[r]=G_NONE;return 0;
}
static unsigned int graph_freeze(struct dep_graph*g,unsigned int seed){g->closed|=graph_closure(g,seed);return g->closed;}
#endif
