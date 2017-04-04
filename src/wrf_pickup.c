#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <errno.h>
#include "constants.h"

#define PI 3.141592653589793238462

#define TOTAL_HEIGHT (12 + 1 + 12 + 12 + 12 + 1 + 1 + 1 + 1 + 1 + 12 + 12 + 12 + 12 + 12 + 1 + 12 + 1 + 1 + 1 + 1 + 12 + 12 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1)
#define TOTAL_SIZE_1HOUR (NX * NY * TOTAL_HEIGHT)

void ll2xy(float grdlat, float grdlon, int *grdi, int *grdj)
{
  double pi, pi2, pi4, d2r, r2d, radius, omega4;
  double gcon,ogcon,H,deg,cn1,cn2,cn3,cn4,rih,xih,yih,rrih,check;
  double alnfix,alon,x,y,windrot;
  double latref,lonref,iref,jref,stdlt1,stdlt2,stdlon,delx,dely;

  pi = M_PI;
  pi2 = pi/2.0;
  pi4 = pi/4.0;
  d2r = pi/180.0;
  r2d = 180.0/pi;
  radius = 6371229.0;
  omega4 = 4.0*pi/86400.0;

  latref = CLAT;
  lonref = CLON;
  iref   = CX;
  jref   = CY;
  stdlt1 = CLAT;
  stdlt2 = CLAT;
  stdlon = CLON;
  delx   = DX;
  dely   = DY;

  gcon = sin(d2r*(fabs(stdlt1)));

  ogcon = 1.0/gcon;
  H = fabs(stdlt1)/(stdlt1);        /* 1 for NHem, -1 for SHem */
  cn1 = sin((90.0-fabs(stdlt1))*d2r);
  cn2 = radius*cn1*ogcon;
  deg = (90.0-fabs(stdlt1))*d2r*0.5;
  cn3 = tan(deg);
  deg = (90.0-fabs(latref))*d2r*0.5;
  cn4 = tan(deg);
  rih = cn2*pow((cn4/cn3),gcon);

  xih =  rih*sin((lonref-stdlon)*d2r*gcon);
  yih = -rih*cos((lonref-stdlon)*d2r*gcon)*H;
  deg = (90.0-grdlat*H)*0.5*d2r;
  cn4 = tan(deg);
  rrih = cn2*pow((cn4/cn3),gcon);
  check  = 180.0-stdlon;
  alnfix = stdlon+check;
  alon   = grdlon+check;

  while (alon<  0.0) alon = alon+360.0;
  while (alon>360.0) alon = alon-360.0;

  deg = (alon-alnfix)*gcon*d2r;
  x =  rrih*sin(deg);
  y = -rrih*cos(deg)*H;
  *grdi = iref + (x-xih)/delx;
  *grdj = jref + (y-yih)/dely;
  windrot=gcon*(stdlon-grdlon)*d2r;
}

float pickup(float *vals, int x, int y)
{
  float v, v1, v2, v3, v4, v5, v6, v7, v8;
  y = y - 1;
  x = x - 1;
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
  FILE *fp, *fpw;
  char station[10], name[256];
  float lat, lon;
  unsigned int pos;
  char elements[][20] = {"W1000", "W925", "W900", "W850", "W800", "W700", "W600", "W500", "W400", "W300", "W200", "W100",
			 "T2",
			 "QV1000", "QV925", "QV900", "QV850", "QV800", "QV700", "QV600", "QV500", "QV400", "QV300", "QV200", "QV100",
			 "QC1000", "QC925", "QC900", "QC850", "QC800", "QC700", "QC600", "QC500", "QC400", "QC300", "QC200", "QC100",
			 "QR1000", "QR925", "QR900", "QR850", "QR800", "QR700", "QR600", "QR500", "QR400", "QR300", "QR200", "QR100",
			 "RAINC", "RAINRC", "RAINNC", "RAINRNC", "SWDOWN",
			 "EPT1000", "EPT925", "EPT900", "EPT850", "EPT800", "EPT700", "EPT600", "EPT500", "EPT400", "EPT300", "EPT200", "EPT100",
			 "G1000", "G925", "G900", "G850", "G800", "G700", "G600", "G500", "G400", "G300", "G200", "G100",
			 "T1000", "T925", "T900", "T850", "T800", "T700", "T600", "T500", "T400", "T300", "T200", "T100",
			 "TH1000", "TH925", "TH900", "TH850", "TH800", "TH700", "TH600", "TH500", "TH400", "TH300", "TH200", "TH100",
			 "TD1000", "TD925", "TD900", "TD850", "TD800", "TD700", "TD600", "TD500", "TD400", "TD300", "TD200", "TD100",
			 "TD2",
			 "RH1000", "RH925", "RH900", "RH850", "RH800", "RH700", "RH600", "RH500", "RH400", "RH300", "RH200", "RH100",
			 "CLFLO", "CLFMI", "CLFHI", "RH2",
			 "U1000", "U925", "U900", "U850", "U800", "U700", "U600", "U500", "U400", "U300", "U200", "U100",
			 "V1000", "V925", "V900", "V850", "V800", "V700", "V600", "V500", "V400", "V300", "V200", "V100",
			 "U10", "V10", "SLP", "DBZ", "CAPE", "CIN", "LCL", "LFC", "PW", "SSI", "SSI700_500", "SSI925_850"
  };
  
  vals = (float*)malloc(sizeof(float) * (TOTAL_SIZE_1HOUR) * TMAX);
  fp = fopen(argv[1], "rb");
  r = fread(vals, sizeof(float), TOTAL_SIZE_1HOUR * TMAX, fp);

  if(r != TOTAL_SIZE_1HOUR * TMAX){
    return -1;
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
    for(t = 0; t < TMAX; t++){
      fprintf(fpw, "Station:%s\tLat:%f\tLon:%f\tFT:%d", station, lat, lon, t);
      for(e = 0; e < TOTAL_HEIGHT; e++){
	float v;
	pos = t * TOTAL_SIZE_1HOUR + e * NX * NY;
	v = pickup(&vals[pos], x, y);
	fprintf(fpw, "\t%s:%f", elements[e], v);
      }
      fprintf(fpw, "\n");
    }
  }
  
  free(vals);
  fclose(fp);
  fclose(fpw);
  
  return 0;
}
