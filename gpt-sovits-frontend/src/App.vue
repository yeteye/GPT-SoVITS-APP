<template>
  <div id="app">
    <div>
      <router-view @add-to-cart="addToCart"></router-view>
    </div>
    <FloatingCart :message="purchaseMessage" />

  </div>
</template>
<script setup>
import {RouterLink,RouterView} from "vue-router"
// import FloatingCart from "@/components/FloatingCart.vue";
import {ref} from "vue";
const purchaseMessage = ref('');
const addToCart = (message) => {
  purchaseMessage.value = message;
}
</script>
<style>

</style>
