#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ENTRIES 10

typedef struct {
    int id;
    char* data;
    int is_valid;
} Entry;

Entry cache[MAX_ENTRIES];

void init_cache() {
    for (int i = 0; i < MAX_ENTRIES; i++) {
        cache[i].is_valid = 0;
    }
}

Entry* add_entry(int id, const char* data) {
    for (int i = 0; i < MAX_ENTRIES; i++) {
        if (!cache[i].is_valid) {
            cache[i].id = id;
            cache[i].data = strdup(data);
            cache[i].is_valid = 1;
            return &cache[i];
        }
    }
    return NULL;
}

void release_entry(Entry* entry) {
    if (entry && entry->is_valid) {
        free(entry->data);
        entry->is_valid = 0;
    }
}

void use_entry(Entry* entry) {
    if (entry && entry->is_valid) {
        printf("Using entry %d: %s\n", entry->id, entry->data);
    } else {
        printf("Invalid entry\n");
    }
}

int main() {
    init_cache();

    Entry* e1 = add_entry(1, "data1");
    Entry* e2 = add_entry(2, "data2");

    use_entry(e1);
    use_entry(e2);

    release_entry(e1);
    release_entry(e1); // Double release

    use_entry(e1); // Use after free

    return 0;
}