/* The base validates quarantine; this enforces critical deferral evidence. */
static int contain_cases_valid(const unsigned int*w,unsigned int epoch,unsigned int mode){
 const unsigned int*c=w+236,*d=w+184,*q=w+204;
 if(mode<1||mode>2||!contain_case_base(w,epoch))return 0;
 if(c[0]!=mode||c[1]!=16||c[2]!=28||c[3]!=40||c[4]<40||c[4]>44||
    c[5]!=2||c[6]!=1||c[7]!=1||c[8]||c[9]!=8||c[10]!=8||
    c[11]!=40||c[12]||c[13]!=12||c[14]!=12||c[15]||c[16]!=24||c[17]!=mode||c[18]||c[19])return 0;
 if(d[2]!=(mode==1?17u:29u)||d[3]<=d[2]||d[3]>=(mode==1?28u:40u)||
    d[7]!=(mode==1?3u:2u)||q[2]!=40||q[3]!=44)return 0;
 return 1;
}
