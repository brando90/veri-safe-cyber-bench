diff --git a/src/cache.c b/src/cache.c
index 2729..newhash 100644
--- a/src/cache.c
+++ b/src/cache.c
@@ -350,6 +350,7 @@ Result cache_evict(Cache *c, const char *id)
     if (e->pins > 0)
         return R_PINNED;
     lru_unlink(c, e);
+    hash_remove(c, e);
     c->count--;
     entry_destroy(c, e);
     c->st.evicted++;
    return R_OK;
 }