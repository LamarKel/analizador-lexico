%{
#include <stdio.h>
void token(const char* tipo, const char* valor){
    printf("%-15s | %s\n", tipo, valor);
}
%}

%%

"if"|"else"|"while"|"for"|"int"|"float"|"return"  { token("PALABRA CLAVE", yytext); }

[a-zA-Z_][a-zA-Z0-9_]*   { token("IDENTIFICADOR", yytext); }

[0-9]+\.[0-9]+            { token("FLOTANTE",      yytext); }
[0-9]+                    { token("ENTERO",         yytext); }

\"[^\"]*\"                { token("CADENA",         yytext); }

"=="|"!="|"<="|">="       { token("OPERADOR",       yytext); }
[+\-*/=<>!]               { token("OPERADOR",       yytext); }

[(){};,]                  { token("DELIMITADOR",    yytext); }

[ \t\n\r]                 { }

.                         { token("ERROR",          yytext); }

%%

int yywrap(){ return 1; }
int main(){ yylex(); return 0; }