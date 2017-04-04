#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <errno.h>
#include "constants.h"

void ll2xy(float grdlat, float grdlon, int *grdi, int *grdj)
{
	*grdi = (int)((grdlon - GSM_WLON) / GSM_DX);
	*grdj = (int)((grdlat - GSM_WLAT) / GSM_DY);
}

float pickup(float *vals, int x, int y)
{
  float v, v1, v2, v3, v4, v5, v6, v7, v8;

  y = y - 1;
  x = x - 1;

  v  = vals[(y    ) * GSM_NX + (x    )];
  v1 = vals[(y + 1) * GSM_NX + (x - 1)];
  v2 = vals[(y + 1) * GSM_NX + (x    )];
  v3 = vals[(y + 1) * GSM_NX + (x + 1)];
  v4 = vals[(y    ) * GSM_NX + (x - 1)];
  v5 = vals[(y    ) * GSM_NX + (x + 1)];
  v6 = vals[(y - 1) * GSM_NX + (x - 1)];
  v7 = vals[(y - 1) * GSM_NX + (x    )];
  v8 = vals[(y - 1) * GSM_NX + (x + 1)];

  return (v + v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8) / 9.;
}

int main(int argc, char* argv[])
{
  int r, i;
  int t, e, k1, k2;
  int x, y;
	int total_size_1hour, tmax;
  float *vals;
  FILE *fp, *fpw;
  char station[10], name[256];
  float lat, lon;
  unsigned int pos;
  char elements_surf[][20] = {
		"MSL", "PRESS", "U10", "V10", "TEMP", "RH", "LCLD", "MCLD", "HCLD", "TCLD", "APCP"
  };
	char elements_upper[][20] = {
		"H1000", "U1000", "V1000", "T1000", "W1000", "RH1000",
		"H975", "U975", "V975", "T975", "W975", "RH975",
		"H950", "U950", "V950", "T950", "W950", "RH950",
		"H925", "U925", "V925", "T925", "W925", "RH925",
		"H900", "U900", "V900", "T900", "W900", "RH900",
		"H850", "U850", "V850", "T850", "W850", "RH850",
		"H800", "U800", "V800", "T800", "W800", "RH800",
		"H700", "U700", "V700", "T700", "W700", "RH700",
		"H600", "U600", "V600", "T600", "W600", "RH600",
		"H500", "U500", "V500", "T500", "W500", "RH500",
		"H400", "U400", "V400", "T400", "W400", "RH400",
		"H300", "U300", "V300", "T300", "W300", "RH300",
		"H250", "U250", "V250", "T250", "W250", 
		"H200", "U200", "V200", "T200", "W200", 
		"H150", "U150", "V150", "T150", "W150", 
		"H100", "U100", "V100", "T100", "W100" 
	};
	char elements_add[][20] = {
		"SSI", "SSI850_700", "SSI925_850", "EPT", "TD850", "TD700"
	};

	i = atoi(argv[4]);
	if(i == 0) {
		// surface
		total_size_1hour = 11;
		k1 = 0;
	} else if(i == 1) {
		// upper
		total_size_1hour = 6 * 12 + 5 * 4;
		k1 = 1;
	} else if(i == 2) {
		// add
		total_size_1hour = 6;
		k1 = 2;
	} else {
		return -12;
	}

	i = atoi(argv[5]);
	if(i == 0){
		if(k1 == 0){
			tmax = 85;
		} else {
			tmax = 29;
		}
		k2 = 0;
	} else if(i == 1){
		if(k1 == 0){
			tmax = 36;
		} else {
			tmax = 18;
		}
		k2 = 1;
	} else if(i == 2){
		if(k1 == 0){
			tmax = 24;
		} else {
			tmax = 12;
		}
		k2 = 2;
	} else {
		return -12;
	}

	
  vals = (float*)malloc(sizeof(float) * (total_size_1hour) * GSM_NX * GSM_NY * tmax);
  fp = fopen(argv[1], "rb");
	if(k1 == 0 && k2 == 0){
		r = fread(vals, sizeof(float), total_size_1hour * GSM_NX * GSM_NY  * tmax - GSM_NX * GSM_NY, fp);
	} else {
		r = fread(vals, sizeof(float), total_size_1hour * GSM_NX * GSM_NY  * tmax, fp);
	}

	if(k1 == 0 && k2 ==0 ){
		if(r != total_size_1hour * GSM_NX * GSM_NY * tmax - GSM_NX * GSM_NY){
			fprintf(stderr, "Size mismatch\n");
			return -1;
		}
	} else {
		if(r != total_size_1hour * GSM_NX * GSM_NY * tmax){
			fprintf(stderr, "Size mismatch\n");
			return -1;
		}
	}
  fclose(fp);

  fp = fopen(argv[2], "r");
  if(fp == NULL){
    fprintf(stderr, "Cannot open %s\n", argv[2]);
    return -2;
  }

  fpw = fopen(argv[3], "w");
  if(fpw == NULL){
    fprintf(stderr, "Cannot open %s\n", argv[3]);
    return -3;
  }
  
  while(r = fscanf(fp, "%s %f %f %s", station, &lat, &lon, name)){
    if(r == EOF){
      break;
    }
    ll2xy(lat, lon, &x, &y);
    if(x < 0 || y < 0){
      continue;
    }
    for(t = 0; t < tmax; t++){
			int pt;
			if(k1 == 0 && k2 == 0){
				pt = t;
			} else if(k1 == 0 && k2 == 1) {
				pt = 87 + t * 3;
			} else if(k1 == 0 && k2 == 2) {
				pt = 195 + t * 3;
			} else if((k1 == 1 || k1 == 2) && k2 == 0) {
				pt = t * 3;
			} else if((k1 == 1 || k1 == 2) && k2 == 1) {
				pt = 90 + t * 6;
			} else if((k1 == 1 || k1 == 2) && k2 == 2) {
				pt = 198 + t * 6;
			} else {
				pt = -1;
			}

      fprintf(fpw, "Station:%s\tLat:%f\tLon:%f\tFT:%d", station, lat, lon, pt);
      for(e = 0; e < total_size_1hour; e++){
				float v;
				if(k1 == 0 && k2 == 0 && e == total_size_1hour - 1 && t == 0) {
					continue;
				}

				if(k1 == 0 && k2 == 0){
					if(t < 2){
						pos = t * (total_size_1hour - 1) * GSM_NX * GSM_NY + e * GSM_NX * GSM_NY;
					} else {
						pos = (t - 1) * total_size_1hour * GSM_NX * GSM_NY + (total_size_1hour - 1) * GSM_NX * GSM_NY + e * GSM_NX * GSM_NY;
					}						
				} else {
					pos = t * total_size_1hour * GSM_NX * GSM_NY + e * GSM_NX * GSM_NY;
				}
				v = pickup(&vals[pos], x, y);
				if(k1 == 0){
					fprintf(fpw, "\t%s:%f", elements_surf[e], v);
				} else if(k1 == 1){
					fprintf(fpw, "\t%s:%f", elements_upper[e], v);
				} else if(k1 == 2){
					fprintf(fpw, "\t%s:%f", elements_add[e], v);
				}	
      }
      fprintf(fpw, "\n");
    }
  }
  
  free(vals);
  fclose(fp);
  fclose(fpw);
  
  return 0;
}
