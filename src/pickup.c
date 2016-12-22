#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "constants.h"

#define PI 3.141592653589793238462

#define TOTAL_HEIGHT (11 + 1 + 11 + 11 + 11 + 1 + 1 + 1 + 1 + 1 + 11 + 11 + 11 + 11 + 11 + 1 + 11 + 1 + 1 + 1 + 1 + 11 + 11 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1)
#define TOTAL_SIZE_1HOUR (NX * NY * TOTAL_HEIGHT)

float calc_distance(float lat1, float lon1, float lat2, float lon2)
{
  double a=6378136.0;
  double e2=0.006694470;

  double rad;
  double N1, x1, y1, z1;
  double N2, x2, y2, z2;
  double h1, h2;
  double r, wr;
  
  h1 = h2 = 0.0;
  
  rad=PI / 180.0;

  if(lon1 < 0) {
    lon1 = 360.0 + lon1;
  }
  lat1 = lat1 * rad;
  lon1 = lon1 * rad;

  if(lon2 < 0){
    lon2 = 360.0 + lon2;
  }
  lat2 = lat2 * rad;
  lon2 = lon2 * rad;

  N1 = a * (sqrt(1.0 - e2 * sin(lat1) * sin(lat1)));
  x1 = (N1 + h1) * cos(lat1) * cos(lon1);  
  y1 = (N1 + h1) * cos(lat1) * sin(lon1);
  z1 = (N1 * (1.0 - e2) + h1) * sin(lat1)+ h1;

  N2 = a * (sqrt(1.0 - e2 * sin(lat2) * sin(lat2)));
  x2 = (N2 + h2) * cos(lat2) * cos(lon2);
  y2 = (N2 + h2) * cos(lat2) * sin(lon2);
  z2 = (N2 * (1.0 - e2) + h2) * sin(lat2)+ h2;  

  r = sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2) + (z1 - z2) * (z1 - z2));
  wr=asin(r / 2 / a);
  return r;
  return a * 2 * wr;
}

void ll2xy(float lat, float lon, int *x, int *y)
{
  int dx, dy;

  double _lat, _lon;
  _lat = lat + CLAT;
  _lon = lon + CLON;

  dx = (int)floor(calc_distance(_lat, lon, _lat, CLON) / DX);
  dy = (int)floor(calc_distance(lat, _lon, CLAT, _lon) / DY);

  if(lon > CLON){
    *x = CX + dx;
  } else {
    *x = CX - dx;
  }

  if(lat > CLAT){
    *y = CY + dy;
  } else {
    *y = CY - dy;
  }

  if(*x > NX || *y > NY || *x < 0 || *y < 0){
    *x = -1;
    *y = -1;
  }
}

float pickup(float *vals, int x, int y)
{
  float v, v1, v2, v3, v4, v5, v6, v7, v8;
  v  = vals[(y    ) * NX + (x    )];
  v1 = vals[(y + 1) * NX + (x - 1)];
  v2 = vals[(y + 1) * NX + (x    )];
  v3 = vals[(y + 1) * NX + (x + 1)];
  v4 = vals[(y    ) * NX + (x - 1)];
  v5 = vals[(y    ) * NX + (x + 1)];
  v6 = vals[(y - 1) * NX + (x - 1)];
  v7 = vals[(y - 1) * NX + (x    )];
  v8 = vals[(y - 1) * NX + (x + 1)];

  return (v + v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8) / 9.;
}

int main(int argc, char* argv[])
{
  int r;
  int t, e;
  int x, y;
  float *vals;
  FILE *fp;
  char station[10], name[256];
  float lat, lon;
  unsigned int pos;
  char elements[][20] = {"W1000", "W925", "W900", "W850", "W700", "W600", "W500", "W400", "W300", "W200", "W100",
			 "T2",
			 "QV1000", "QV925", "QV900", "QV850", "QV700", "QV600", "QV500", "QV400", "QV300", "QV200", "QV100",
			 "QC1000", "QC925", "QC900", "QC850", "QC700", "QC600", "QC500", "QC400", "QC300", "QC200", "QV100",
			 "QR1000", "QR925", "QR900", "QR850", "QR700", "QR600", "QR500", "QR400", "QR300", "QR200", "QR100",
			 "RAINC", "RAINRC", "RAINNC", "RAINRNC", "SWDOWN",
			 "EPT1000", "EPT925", "EPT900", "EPT850", "EPT700", "EPT600", "EPT500", "EPT400", "EPT300", "EPT200", "EPT100",
			 "G1000", "G925", "G900", "G850", "G700", "G600", "G500", "G400", "G300", "G200", "G100",
			 "T1000", "T925", "T900", "T850", "T700", "T600", "T500", "T400", "T300", "T200", "T100",
			 "TH1000", "TH925", "TH900", "TH850", "TH700", "TH600", "TH500", "TH400", "TH300", "TH200", "TH100",
			 "TD1000", "TD925", "TD900", "TD850", "TD700", "TD600", "TD500", "TD400", "TD300", "TD200", "TD100",
			 "TD2",
			 "RH1000", "RH925", "RH900", "RH850", "RH700", "RH600", "RH500", "RH400", "RH300", "RH200", "RH100",
			 "CLFLO", "CLFMI", "CLFHI", "RH2",
			 "U1000", "U925", "U900", "U850", "U700", "U600", "U500", "U400", "U300", "U200", "U100",
			 "V1000", "V925", "V900", "V850", "V700", "V600", "V500", "V400", "V300", "V200", "V100",
			 "U10", "V10", "SLP", "DBZ", "CAPE", "CIN", "LCL", "LFC", "SSI", "SSI700_500", "SSI925_850"
  };
  
  vals = (float*)malloc(sizeof(float) * (TOTAL_SIZE_1HOUR) * TMAX);
  fp = fopen(argv[1], "rb");
  r = fread(vals, sizeof(float), TOTAL_SIZE_1HOUR * TMAX, fp);
  printf("%d %d\n", r, TOTAL_SIZE_1HOUR * 2);
  if(r != TOTAL_SIZE_1HOUR * TMAX){
    return -1;
  }
  fclose(fp);

  fp = fopen(argv[2], "r");
  if(fp == NULL){
    fprintf(stderr, "Cannot open %s\n", argv[2]);
    return -2;
  }
  while(r = fscanf(fp, "%s %f %f %s", station, &lat, &lon, name)){
    if(r == EOF){
      break;
    }
    ll2xy(lat, lon, &x, &y);
    if(x < 0 || y < 0){
      continue;
    }
    for(t = 0; t < TMAX; t++){
      printf("Station:%s\tLat:%f\tLon:%f\tFT:%d", station, lat, lon, t);
      for(e = 0; e < TOTAL_HEIGHT; e++){
	float v;
	pos = t * TOTAL_SIZE_1HOUR + e * NX * NY;
	v = pickup(&vals[pos], x, y);
	printf("\t%s:%f", elements[e], v);
      }
      printf("\n");
    }
  }
  
  free(vals);

  return 0;
}
