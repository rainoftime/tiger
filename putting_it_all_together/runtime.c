#include <stdio.h>
#include <stdlib.h>
#include <string.h>

long long *init_record(long long size){
  long long i;
  long long *p, *a;
  p = a = (long long *)malloc(size);
  for(i=0;i<size;i+=sizeof(long long)) *p++ = 0;
  return a;
}

long long char_to_num(char* str){
    if ( strlen(str) ) return (long long)str[0];
    return -1;
}

void exit_program(long long status){
  exit(status);
}

void flush(){
 fflush(stdout);
}

long long *init_array(long long size, long long init){
  long long i;
  long long *a = (long long *)malloc(size*sizeof(long long));
  for(i=0;i<size;i++) a[i]=init;
  return a;
}

long long not(long long n){
  return n==0;
}

char* num_to_char(long long n){
  if ( n < 0 || n >= 256 ) {
    printf("Out of range char! Arguments: %lld\n", n);
    exit(1);
  }

  char *result = (char*) malloc(sizeof(char) * 2);
  result[0] = (char)n;
  result[1] = '\0';
  return result;
}


void print_num(long long n){
  printf("%lld\n", n);
}

void print_string(char *str){
  printf("%s", str);
}

char* read_char(){
  char *c = (char*) malloc(sizeof(char) * 2);
  long long result = getchar();
  // Check EOF.
  if(result < 0)
    result = 0;
  c[0] = result;
  c[1] = '\0';
  return c;
}

long long read_num(){
  long long n;
  scanf("%lld", &n);
  return n;
}

long long string_compare(char *str1, char *str2){
  return strcmp(str1, str2);
}

char* string_concat(char *first, char *second){
  // Reserve space for both strings + '\0'.
  long long combined_length = strlen(first) + strlen(second) + 1;
  char *result = (char*) malloc(combined_length * sizeof(char));
  result[0] = '\0';
  strcat(result, first);
  strcat(result, second);
  return result;
}

long long string_equal(char *str1, char *str2){
  return strcmp(str1, str2) == 0;
}

long long string_length(char *str){
  return strlen(str);
}

char* string_substring(char *source, long long start, long long length){
  if(start < 0  || start + length > strlen(source)){
    printf("Out of range substring! Arguments: \"%s\" %lld %lld \n", source, start, length);
    exit(1);
  }

  // Reserve space for the substring + '\0'.
  char* result = (char*) malloc(sizeof(char) * (length + 1));
  strncpy(result, source + start, length);
  result[length] = '\0';
  return result;
}

long long tigermain(long long);
long long main(){
  printf("\n");
  return tigermain(0 /*static link*/);
}