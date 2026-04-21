#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void print_flag() {
  FILE* f = fopen("flag.txt", "r");
  if (f) {
    char flag[64];
    fgets(flag, sizeof(flag), f);
    printf("Flag: %s\n", flag);
    fclose(f);
  } else {
    printf("flag.txt not found.\n");
  }
}

int main() {
  int coins = 1;
  int bet;
  srand(time(NULL));

  printf(" __  __ __ __ __                     __             \n");
  printf("|  |/  |__|  |__|.-----.-----.---.-.|__|.----.-----.\n");
  printf("|     <|  |  |  ||  _  |     |  _  ||  ||   _|  -__|\n");
  printf("|__|\\__|__|__|__||_____|__|__|___._||__||__| |_____|\n\n");

  printf("Goal: 1000 coins in 10 rounds\n\n");

  for (int i = 0; i < 10; i++) {
    printf("Round %d | Coins: %d\nBet: ", i + 1, coins);
    if (scanf("%d", &bet) != 1) break;

    if (bet > coins) {
      printf("Invalid bet.\n");
      continue;
    }

    if (rand() % 2 == 0) {
      int gain = (bet * (rand() % 301)) / 100;
      coins += gain;
      printf("Result: SUCCESS (Gain: %d)\n", gain);
    } else {
      coins -= bet;
      printf("Result: FAILURE (Lost: %d)\n", bet);
    }

    if (coins == 0) {
      printf("\nYou lost all your coins...\n\n");
      break;
    }

    if (coins >= 1000) {
      print_flag();
      return 0;
    }
    printf("----------------------------------------\n");
  }

  printf("Game Over.\n");
  return 0;
}