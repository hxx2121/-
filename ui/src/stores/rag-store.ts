import { defineStore } from "pinia"
import { computed } from "vue"
import { useStorage } from "@vueuse/core"

export const useRagStore = defineStore("rag", () => {
  const selectedCollectionId = useStorage<number | null>("rag_selected_collection_id", null)
  const isCollectionSelected = computed(() => typeof selectedCollectionId.value === "number" && selectedCollectionId.value > 0)

  function setSelectedCollectionId(collectionId: number | null) {
    selectedCollectionId.value = collectionId
  }

  return { selectedCollectionId, isCollectionSelected, setSelectedCollectionId }
})

