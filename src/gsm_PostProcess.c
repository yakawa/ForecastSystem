#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "constants.h"

#define TOTAL_HEIGHT (6 * 12 + 5 * 4)
#define TOTAL_SIZE_1HOUR (GSM_NX * GSM_NY * TOTAL_HEIGHT)

float _calc_td(float t, float rh)
{
	float es, e;
	float A;
	t = t + 273.15;
  es = 6.112 * exp((17.67 * (t - 273.15)) / (t - 29.65));
	e = es * rh;
	A = log(e / 6.112);
	return 1. / ( (1. / 273.2) - (461. / 2500000.) * log(e / 6.11));
}

void calc_td(float* t, float* rh, float* td)
{
	int i, j, p;

	for(j = 0; j < GSM_NY; j++){
		for(i = 0; i < GSM_NX; i++){
			p = j * GSM_NX + i;
			td[p] = _calc_td(t[p] - 273.15, rh[p] / 100.);
		}
	}
}

float _calc_ept(float p, float t, float td)
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

void calc_ept(float press, float* t, float* td, float* ept)
{
	int i, j, p;

	for(j = 0; j < GSM_NY; j++){
		for(i = 0; i < GSM_NX; i++){
			p = j * GSM_NX + i;
			ept[p] = _calc_ept(press, t[p] - 273.15, td[p] - 273.15);
			//printf("%f %f %f\n", ept[p], t[p], td[p]);
		}
	}
}

void calc_ssi(float* lowerT, float* lowerTd, float* upperT, float lowerPress, float upperPress, float* ssi)
{
  int i, j, p;

  for(j = 0; j < GSM_NY; j++){
    for(i = 0; i < GSM_NX; i++){
      float lowerEPT;
      float t1, t2, t3;
      int loop;
      
      p = j * GSM_NX + i;

      //printf("lowerPress-> %f, T -> %f, Td -> %f\n", lowerPress, lowerT[p], lowerTd[p]);
      lowerEPT = _calc_ept(lowerPress, lowerT[p] - 273.15, lowerTd[p] - 273.15);

      t1 = -80;
      t2 = 80;
      loop = 0;

      while(1){
				float ept1, ept2, er1, er2;
				
				ept1 = _calc_ept(upperPress, t1, t1);
				er1 = ept1 - lowerEPT;

				//printf("ept1->%f, lower->%f\n", ept1, lowerEPT);
				if(isnan(ept1)){
					t2 = ept1;
					break;
				}
				if(loop == 10000){
					t2 = ERROR;
					break;
				}
				if(abs(er1) < 0.001){
					break;
				}
				ept2 = _calc_ept(upperPress, t2, t2);
				er2 = ept2 - lowerEPT;
				if(er1 * er2 < 0){
					t2 = t2 - (t2 - t1) / 2.;
				} else {
					t3 = t1;
					t1 = t2;
					t2 = t2 + (t2 - t3) / 2.;
				}
				loop += 1;
      }
      
      if(isnan(t2)){
				ssi[p] = ERROR;
      } else {
				ssi[p] = (upperT[p] - 273.15) - t2;
      }
			//printf("SSI: %f\n", ssi[p]);
    }
  }
}

int main(int argc, char* argv[])
{
  int hour, tmax = 0, i;
  FILE *fp, *fpw;
  float *vals;
  float *SSI, *SSI850_700, *SSI925_850, *EPT, *TD850, *TD925, *TD700;
  int size;

	i = atoi(argv[3]);
	if(i == 0){
		tmax = 29;
	}
	if(i == 1){
		tmax = 18;
	}
	if(i == 2){
		tmax = 12;
	}
	if(tmax == 0){
		fprintf(stderr, "Filename mismatch\n");
		return -10;
	}
	
  vals = (float*)malloc(sizeof(float) * TOTAL_SIZE_1HOUR * tmax);
	EPT = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
  SSI = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
  SSI850_700 = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
  SSI925_850 = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
	TD850 = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
	TD925 = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
	TD700 = (float*)malloc(sizeof(float) * GSM_NX * GSM_NY);
	
  if(vals == NULL || SSI == NULL || SSI850_700 == NULL || SSI925_850 == NULL || EPT == NULL || TD850 == NULL || TD925 == NULL || TD700 == NULL){
    fprintf(stderr, "Memory Allocation Error\n");
    return -5;
  }
  
  fp = fopen(argv[1], "rb");
  if(fp == NULL){
    fprintf(stderr, "Cannot OPEN File");
    return -1;
  }
  size = fread(vals, sizeof(float), TOTAL_SIZE_1HOUR * tmax, fp);
  if(size != TOTAL_SIZE_1HOUR * tmax){
    printf("%d (%d)\n", size, TOTAL_SIZE_1HOUR * tmax);
    return -2;
  }
  fclose(fp);

  fpw = fopen(argv[2], "wb");

  for(hour = 0; hour < tmax; hour++){
    printf("T = %d\n", hour);
    int c;
		int posH1000 = (GSM_NX * GSM_NY) * 0;
		int posU1000 = (GSM_NX * GSM_NY) * 1;
		int posV1000 = (GSM_NX * GSM_NY) * 2;
		int posT1000 = (GSM_NX * GSM_NY) * 3;
		int posW1000 = (GSM_NX * GSM_NY) * 4;
		int posR1000 = (GSM_NX * GSM_NY) * 5;
		int posH975 = (GSM_NX * GSM_NY) * 6;
		int posU975 = (GSM_NX * GSM_NY) * 7;
		int posV975 = (GSM_NX * GSM_NY) * 8;
		int posT975 = (GSM_NX * GSM_NY) * 9;
		int posW975 = (GSM_NX * GSM_NY) * 10;
		int posR975 = (GSM_NX * GSM_NY) * 11;
		int posH950 = (GSM_NX * GSM_NY) * 12;
		int posU950 = (GSM_NX * GSM_NY) * 13;
		int posV950 = (GSM_NX * GSM_NY) * 14;
		int posT950 = (GSM_NX * GSM_NY) * 15;
		int posW950 = (GSM_NX * GSM_NY) * 16;
		int posR950 = (GSM_NX * GSM_NY) * 17;
		int posH925 = (GSM_NX * GSM_NY) * 18;
		int posU925 = (GSM_NX * GSM_NY) * 19;
		int posV925 = (GSM_NX * GSM_NY) * 20;
		int posT925 = (GSM_NX * GSM_NY) * 21;
		int posW925 = (GSM_NX * GSM_NY) * 22;
		int posR925 = (GSM_NX * GSM_NY) * 23;
		int posH900 = (GSM_NX * GSM_NY) * 24;
		int posU900 = (GSM_NX * GSM_NY) * 25;
		int posV900 = (GSM_NX * GSM_NY) * 26;
		int posT900 = (GSM_NX * GSM_NY) * 27;
		int posW900 = (GSM_NX * GSM_NY) * 28;
		int posR900 = (GSM_NX * GSM_NY) * 29;
		int posH850 = (GSM_NX * GSM_NY) * 30;
		int posU850 = (GSM_NX * GSM_NY) * 31;
		int posV850 = (GSM_NX * GSM_NY) * 32;
		int posT850 = (GSM_NX * GSM_NY) * 33;
		int posW850 = (GSM_NX * GSM_NY) * 34;
		int posR850 = (GSM_NX * GSM_NY) * 35;
		
		
		
		int posT700 = (GSM_NX * GSM_NY) * 45;
		int posT500 = (GSM_NX * GSM_NY) * 57;
    float v;

    c = hour * TOTAL_HEIGHT * GSM_NY * GSM_NX;
		calc_td(&vals[posT850 + c], &vals[posR850 + c], TD850);
		calc_ept(850., &vals[posT850 + c], TD850, EPT);
    calc_ssi(&vals[posT850 + c], TD850, &vals[posT500 + c], 850., 500., SSI);

    calc_ssi(&vals[posT850 + c], TD850, &vals[posT700 + c], 850., 700., SSI850_700);

		calc_td(&vals[posT925 + c], &vals[posR925 + c], TD925);
		calc_ssi(&vals[posT925 + c], TD925, &vals[posT850 + c], 925., 850., SSI925_850);

		calc_td(&vals[posT850 + c], &vals[posR850 + c], TD700);
		
    fwrite(SSI, sizeof(float), GSM_NX * GSM_NY, fpw);
    fwrite(SSI850_700, sizeof(float), GSM_NX * GSM_NY, fpw);
    fwrite(SSI925_850, sizeof(float), GSM_NX * GSM_NY, fpw);
		fwrite(EPT, sizeof(float), GSM_NX * GSM_NY, fpw);
    fwrite(TD850, sizeof(float), GSM_NX * GSM_NY, fpw);
    fwrite(TD700, sizeof(float), GSM_NX * GSM_NY, fpw);		
  }

 
  fclose(fpw);
  
  free(vals);
  free(SSI);
  free(SSI850_700);
  free(SSI925_850);
	free(EPT);
	free(TD925);
	free(TD850);
	free(TD700);
  return 0;
}
