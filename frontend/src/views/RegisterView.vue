<template>
  <div class="min-h-screen flex items-center justify-center bg-cp-black" style="background: radial-gradient(ellipse at 50% 0%, #0D1828 0%, #050A0E 70%);">
    <div class="bg-cp-surface rounded-xl p-8 w-full max-w-md border border-cp-border" style="box-shadow: 0 0 40px rgba(0,240,255,0.06);">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-cp-yellow tracking-widest uppercase">{{ brandName }}</h1>
        <p class="text-cp-muted mt-2">Create your account</p>
      </div>
      <RegisterForm />
      <div class="text-center mt-6">
        <p class="text-cp-muted">
          Already have an account?
          <router-link to="/login" class="text-cp-cyan hover:text-cp-cyan/80 font-medium">
            Sign in
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import RegisterForm from '../components/auth/RegisterForm.vue'
import { BRAND_NAME } from '../config/brand'
const brandName = BRAND_NAME
</script>
