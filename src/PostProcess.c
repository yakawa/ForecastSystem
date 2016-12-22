#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "constants.h"

#define TOTAL_HEIGHT (11 + 1 + 11 + 11 + 11 + 1 + 1 + 1 + 1 + 1 + 11 + 11 + 11 + 11 + 11 + 1 + 11 + 1 + 1 + 1 + 1 + 11 + 11 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1)
#define TOTAL_SIZE_1HOUR (NX * NY * TOTAL_HEIGHT)

void _swapbytes(void *pv, size_t n)
{
  char *p = pv;
  size_t lo, hi;
  for(lo=0, hi=n-1; hi>lo; lo++, hi--)
    {
      char tmp=p[lo];
      p[lo] = p[hi];
      p[hi] = tmp;
    }
}

void SwapBytes(float *vals)
{
  int i, j, k, t;
  for(t = 0; t < TMAX; t++){
    for(k = 0; k < TOTAL_HEIGHT; k++){
      for(j = 0; j < NY; j++){
	for(i = 0; i < NX; i++){
	  _swapbytes(&vals[i + j * NX + k * NX * NY + t * NX * NY * TOTAL_HEIGHT], sizeof(float));
	}
      }
    }
  }
}

float calc_ept(float p, float t, float td)
{
  float term1, term2, e, es, x;
  float Tlcl;

  t = t + 273.15;
  td = td + 273.15;

  term1 = 1. / (td - 56.);
  term2 = log(t / td) / 800.;
  Tlcl = 1. / (term1 + term2) + 56.;

  e = 6.112 * exp((17.67 * (td - 273.15)) / (td - 29.65));
  es = 6.112 * exp((17.67 * (t - 273.15)) / (t - 29.65));
  x = 0.622 * (e / (p -e));
  return  t * pow(1000./(p - e), 0.2854) * pow(t / Tlcl, 0.28 * x) * exp( (3036. / Tlcl - 1.78) * x * (1 + 0.448 * x));
}

void calc_ssi(float* lowerT, float* lowerTd, float* upperT, float lowerPress, float upperPress, float* ssi)
{
  int i, j, p;
  #pragma omp for
  for(j = 0; j < NY; j++){
    for(i = 0; i < NX; i++){
      float lowerEPT;
      float t1, t2, t3;
      
      p = j * NX + i;

      lowerEPT = calc_ept(lowerPress, lowerT[p], lowerTd[p]);

      t1 = -50;
      t2 = 50;

      while(1){
	float ept1, ept2, er1, er2;

	ept1 = calc_ept(upperPress, t1, t1);
	er1 = ept1 - lowerEPT;

	if(isnan(ept1)){
	  t2 = ept1;
	  break;
	}
	if(er1 * er1 < 0.001){
	  break;
	}
	ept2 = calc_ept(upperPress, t2, t2);
	er2 = ept2 - lowerEPT;
	if(er1 * er2 < 0){
	  t2 = t2 - (t2 - t1) / 2.;
	} else {
	  t3 = t1;
	  t1 = t2;
	  t2 = t2 + (t2 - t3) / 2.;
	}		  
      }
      if(isnan(t2)){
	ssi[p] = ERROR;
      } else {
	ssi[p] = upperT[p] - t2;
      }
    }
  }
}

int main(int argc, char* argv[])
{
  int hour;
  FILE *fp, *fpw;
  float *vals;
  float *SSI, *SSI850_700, *SSI925_850;
  int size;

  vals = (float*)malloc(sizeof(float) * TOTAL_SIZE_1HOUR * TMAX);
  SSI = (float*)malloc(sizeof(float) * NX * NY);
  SSI850_700 = (float*)malloc(sizeof(float) * NX * NY);
  SSI925_850 = (float*)malloc(sizeof(float) * NX * NY);
  
  fp = fopen(argv[1], "rb");
  if(fp == NULL){
    fprintf(stderr, "Cannot OPEN File");
    return -1;
  }
  size = fread(vals, sizeof(float), TOTAL_SIZE_1HOUR * TMAX, fp);
  if(size != TOTAL_SIZE_1HOUR * TMAX){
    return -2;
  }
  fclose(fp);

  SwapBytes(vals);
  fpw = fopen(argv[2], "wb");

  for(hour = 0; hour < TMAX; hour++){
    int c;
    int posT925 = (NX * NY) * 72 + (NX * NY) * 1;
    int posT850 = (NX * NY) * 72 + (NX * NY) * 4;
    int posT700 = (NX * NY) * 72 + (NX * NY) * 5;
    int posT500 = (NX * NY) * 72 + (NX * NY) * 7;
    int posTd925 = (NX * NY) * 94 + (NX * NY) * 1;
    int posTd850 = (NX * NY) * 94 + (NX * NY) * 4;
    int posTd700 = (NX * NY) * 94 + (NX * NY) * 5;
    float v;

    c = hour * TOTAL_HEIGHT * NY * NX;
    
    calc_ssi(&vals[posT850 + c], &vals[posTd850 + c], &vals[posT500 + c], 850., 500., SSI);
    calc_ssi(&vals[posT850 + c], &vals[posTd850 + c], &vals[posT700 + c], 850., 700., SSI850_700);
    calc_ssi(&vals[posT925 + c], &vals[posTd925 + c], &vals[posT850 + c], 925., 850., SSI925_850);
    v = vals[posT850 + c];
    fwrite(&vals[c], sizeof(float), TOTAL_SIZE_1HOUR, fpw);
    fwrite(SSI, sizeof(float), NX * NY, fpw);
    fwrite(SSI850_700, sizeof(float), NX * NY, fpw);
    fwrite(SSI925_850, sizeof(float), NX * NY, fpw);
  }

 
  fclose(fpw);
  
  free(vals);
  free(SSI);
  free(SSI850_700);
  free(SSI925_850);
  return 0;
}
