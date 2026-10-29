#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAX_SESSIONS 10

typedef struct {
    char name[64];
    int refcount;
} Session;

Session* cache[MAX_SESSIONS];
int cache_size = 0;

void create_session(const char* name) {
    if (cache_size >= MAX_SESSIONS) {
        printf("Error: Cache full\n");
        return;
    }

    Session* s = malloc(sizeof(Session));
    strcpy(s->name, name);
    s->refcount = 1;
    cache[cache_size++] = s;
    printf("Created %s\n", name);
}

void get_session(const char* name) {
    for (int i = 0; i < cache_size; i++) {
        if (strcmp(cache[i]->name, name) == 0) {
            cache[i]->refcount++;
            printf("Got %s\n", name);
            return;
        }
    }
    printf("Error: %s not found\n", name);
}

void delete_session(const char* name) {
    for (int i = 0; i < cache_size; i++) {
        if (strcmp(cache[i]->name, name) == 0) {
            cache[i]->refcount--;
            if (cache[i]->refcount == 0) {
                free(cache[i]);
                cache[i] = cache[cache_size-1];
                cache_size--;
                printf("Deleted %s\n", name);
            } else {
                printf("Reference count for %s is now %d\n", name, cache[i]->refcount);
            }
            return;
        }
    }
    printf("Error: %s not found\n", name);
}

void list_sessions() {
    if (cache_size == 0) {
        printf("(empty)\n");
        return;
    }

    for (int i = 0; i < cache_size; i++) {
        printf("%s\n", cache[i]->name);
    }
}

int main() {
    char line[128];
    while (fgets(line, sizeof(line), stdin)) {
        char cmd[16];
        sscanf(line, "%s", cmd);

        if (strcmp(cmd, "create") == 0) {
            char name[64];
            sscanf(line, "create %s", name);
            create_session(name);
        } else if (strcmp(cmd, "get") == 0) {
            char name[64];
            sscanf(line, "get %s", name);
            get_session(name);
        } else if (strcmp(cmd, "delete") == 0) {
            char name[64];
            sscanf(line, "delete %s", name);
            delete_session(name);
        } else if (strcmp(cmd, "list") == 0) {
            list_sessions();
        }
    }
    return 0;
}