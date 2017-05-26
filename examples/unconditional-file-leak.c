#include <stdio.h>

void test (const char *filename)
{
  int i;
  FILE *f;
  f = fopen (filename, "w");
  for (i = 0; i < 10; i++)
    fprintf (f, "%i: %i",  i,  i * i);
}
