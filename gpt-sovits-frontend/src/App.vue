<template>
  <div id="app">
    <div>
      <HeaderBar v-if="!route.meta.hideHeader" />
      <router-view @add-to-cart="addToCart"></router-view>
    </div>
    <FloatingCart :message="purchaseMessage" />

  </div>
</template>
<script setup>
import { useRoute } from 'vue-router'
import HeaderBar from '@/components/HeaderBar.vue'
import {ref} from "vue";
const purchaseMessage = ref('');
const addToCart = (message) => {
  purchaseMessage.value = message;
}

const route = useRoute()
</script>
<style>

</style>
