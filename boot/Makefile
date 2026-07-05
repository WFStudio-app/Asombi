CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c11 -D_GNU_SOURCE
TARGET = os

$(TARGET): src/main.c
	$(CC) $(CFLAGS) -o $(TARGET) src/main.c

arm64:
	aarch64-linux-gnu-gcc $(CFLAGS) -o $(TARGET)-arm64 src/main.c

clean:
	rm -f $(TARGET) $(TARGET)-arm64
