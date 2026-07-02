# VzlaUnida - Plataforma de Reubicación de Familias

[![Django](https://img.shields.io/badge/Django-6.0-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Descripción del Proyecto

**VzlaUnida** es una plataforma web desarrollada en Django que conecta a **Huéspedes** (personas con disponibilidad de alojamiento) con **Afectados** (personas que requieren refugio) en el contexto de Venezuela.

### 🎯 Objetivo General

Facilitar la reubicación familiar en situaciones de emergencia, cumpliendo con los lineamientos internacionales de protección de identidad para menores y personas en situación de vulnerabilidad.

---

## ✨ Características Principales

### 🔐 Sistema de Autenticación
- Registro de usuarios con email único
- Inicio/Cierre de sesión seguro
- Redirección automática según perfil
- Rate Limiting: 5 intentos/minuto en login

### 👤 Gestión de Huéspedes
- Registro completo con datos personales
- Validación de cédula (V/E) y email único
- Subida de documentos (cédula y residencia)
- Sistema de verificación en 5 pasos
- Dashboard personalizado

### 🔍 Sistema de Verificación
- **5 estados:**
  - ⏳ Pendiente de revisión
  - 🔍 En revisión
  - ✅ Aprobado
  - ❌ Rechazado
  - 📝 Requiere corrección
- Comentarios del administrador
- Fecha de verificación registrada
- Notificaciones automáticas por email

### 📊 Dashboard Personalizado
- Información del perfil
- Estado de verificación con colores
- Estadísticas de afectados por ubicación
- Lista de afectados cercanos
- Lista de otros huéspedes verificados

### 🛡️ Panel de Administración
- Gestión completa de huéspedes
- Acciones individuales y masivas
- Visualización de documentos
- Filtros y búsqueda avanzada

### 📧 Sistema de Notificaciones
- Email de bienvenida al registrarse
- Notificaciones al cambiar estado de verificación

### 🔒 Seguridad
- Variables de entorno con `python-dotenv`
- Rate Limiting en login (5/m) y registro (3/m)
- CORS configurado
- Headers de seguridad (HSTS, X-Frame-Options, Referrer-Policy)

---

# 📋 Historial de Cambios - VzlaUnida

> **Estado del proyecto:** 🚀 En desarrollo activo  
> **Última actualización:** `01/07/2026 20:03:45`

---

## 🚀 Inicio del Proyecto

### ✅ Commit 1: `Commit inicial: Estructura base de Django`
- **Fecha:** `27/06/2026 18:39:22`
- **Descripción:** Creación de la estructura base del proyecto Django.
- **Cambios principales:**
  - Configuración inicial de Django.
  - Estructura de carpetas del proyecto.
  - Configuración base de `settings.py`.
  - Primeros modelos y vistas básicas.

---

## 🏗️ Fase 1: Registro de Huéspedes

### ✅ Commit 2: `Registro de huesped basico con carga de archivos`
- **Fecha:** `27/06/2026 19:59:09`
- **Descripción:** Implementación del formulario básico de registro de huéspedes.
- **Cambios principales:**
  - Formulario de registro de huéspedes.
  - Modelo `Huesped` con campos básicos.
  - Carga de archivos (cédula y residencia).
  - Dashboard básico.
  - Rutas principales.

### ✅ Commit 3: `Finalizada integración de formulario: campos dinámicos de ciudad, validación corregida y subida de archivos funcionando`
- **Fecha:** `28/06/2026 00:25:27`
- **Descripción:** Mejora del formulario de registro con funcionalidades avanzadas.
- **Cambios principales:**
  - Campos dinámicos de ciudad según estado.
  - Validación de ciudad/estado.
  - Subida de archivos funcionando correctamente.
  - Validaciones de formulario mejoradas.

---

## 🐛 Fase 2: Correcciones y Mejoras

### ✅ Commit 4: `Errores en el modelo Huesped y bloquedo media/ en .gitignore`
- **Fecha:** `28/06/2026 14:35:45`
- **Descripción:** Corrección de errores en el modelo y configuración de `.gitignore`.
- **Cambios principales:**
  - Corrección de errores en el modelo `Huesped`.
  - Agregado `media/` a `.gitignore`.
  - Ajustes en el panel de administración.
  - Correcciones de campos en el modelo.

### ✅ Commit 5: `Mejoras en el registro de huéspedes`
- **Fecha:** `28/06/2026 22:52:15`
- **Descripción:** Optimización del proceso de registro.
- **Cambios principales:**
  - Validación de email único.
  - Validación de cédula única (V/E).
  - Formato automático de cédula con puntos.
  - Validación de archivos (extensiones y tamaño).
  - Mejoras en el dashboard.

---

## 🎨 Fase 3: Diseño y UI

### ✅ Commit 6: `Cambios generales en registro`
- **Fecha:** `30/06/2026 17:45:31`
- **Descripción:** Rediseño general del formulario de registro.
- **Cambios principales:**
  - Rediseño del formulario de registro.
  - Mejoras en la experiencia de usuario.
  - Indicador de pasos.
  - Estilos mejorados con Tailwind.

---

## 🔍 Fase 4: Sistema de Verificación

### ✅ Commit 7: `feat: Implementación completa del sistema de validación de huéspedes`
- **Fecha:** `30/06/2026 22:17:47`
- **Descripción:** Sistema completo de verificación de huéspedes.
- **Cambios principales:**
  - Sistema de 5 estados de verificación.
  - Panel de administración mejorado.
  - Acciones individuales y masivas.
  - Comentarios del administrador.
  - Fecha de verificación registrada.
  - Notificaciones automáticas por email.
  - Dashboard con estado visual.
  - Validaciones de email y cédula única.
  - Redirecciones de seguridad.
  - Corrección de rutas.

---

## 🎨 Fase 5: Diseño Final

### ✅ Commit 8: `Mejoras de frontend - Sistema de diseño VzlaEncuentra`
- **Fecha:** `30/06/2026 23:28:34`
- **Descripción:** Rediseño completo de la interfaz basado en la bandera de Venezuela.
- **Cambios principales:**
  - Paleta de colores institucional: Amarillo (`#FFD100`), Azul (`#001F5C`), Rojo (`#CF202F`).
  - Tipografía: Inter (geométrica, moderna).
  - Sistema de diseño en `styles.css`.
  - Banners con colores de la bandera.
  - Tarjetas con efectos hover y brillo.
  - Diseño responsive.

### ✅ Commit 9: `Mejoras de frontend - Sistema de diseño VzlaEncuentra`
- **Fecha:** `30/06/2026 23:39:03`
- **Descripción:** Segunda fase de mejoras visuales y experiencia de usuario.
- **Cambios principales:**
  - Dashboard compacto sin scroll vertical externo.
  - Estadísticas en tarjetas reducidas.
  - Scroll interno para listas largas.
  - Fondo con gradiente en la Home.
  - Footer con información de contacto.
  - Efecto hover mejorado en tarjetas.
  - Corrección de espaciados y tamaños.

---

## 🔐 Fase 6: Seguridad

### ✅ Commit 10: `feat: Fase 1 - Seguridad Crítica implementada y probada`
- **Fecha:** `01/07/2026 20:03:45`
- **Descripción:** Implementación de medidas de seguridad avanzadas.
- **Cambios principales:**
  - Variables de entorno aisladas con `python-dotenv` (`.env`).
  - Rate Limiting en login: 5 intentos/minuto.
  - Rate Limiting en registro: 3 intentos/minuto.
  - CORS configurado correctamente para entornos de producción.
  - Headers de seguridad robustos: HSTS, X-Frame-Options, Referrer-Policy.
  - Configuración de caché dedicada para rate limiting.
  - Silenciamiento de advertencias en desarrollo.
  - Pruebas de Rate Limiting completadas con éxito (`403 Forbidden`).

---

## 📊 Resumen del Proyecto

| Fase | Funcionalidad | Estado | Fecha |
| :---: | :--- | :---: | :---: |
| **1** | Estructura base de Django | ✅ Completado | 27/06 |
| **2** | Registro de huéspedes básico | ✅ Completado | 27/06 |
| **3** | Campos dinámicos y validaciones | ✅ Completado | 28/06 |
| **4** | Correcciones de modelo y `.gitignore` | ✅ Completado | 28/06 |
| **5** | Mejoras en registro y validaciones | ✅ Completado | 28/06 |
| **6** | Cambios generales en registro | ✅ Completado | 30/06 |
| **7** | Sistema de validación completo | ✅ Completado | 30/06 |
| **8** | Diseño inicial (VzlaEncuentra) | ✅ Completado | 30/06 |
| **9** | Diseño final y UX mejorada | ✅ Completado | 30/06 |
| **10** | Seguridad avanzada (Fase 1) | ✅ Completado | 01/07 |

---

## 📈 Estadísticas Consolidadas

| Métrica | Valor |
| :--- | :--- |
| **Total de commits** | 10 |
| **Duración del desarrollo** | 4 días (27/06 - 01/07) |
| **Archivos modificados** | +30 |
| **Modelos base** | 2 (`Huesped`, `Afectado`) |
| **Vistas / Pantallas** | 5 |
| **Estados de verificación** | 5 |
| **Pruebas de estrés completadas** | ✅ 10/10 |

---

## 🔜 Próximos Pasos

1. 🔐 **Fase 2 de Seguridad:** Integración de logging estructurado y alertas con Sentry.
2. 📝 **Registro de Afectados:** Desarrollo del modelo completo y su respectivo formulario web.
3. 🔀 **Sistema de Matches:** Diseño del algoritmo para la coincidencia automática de datos.
4. 📱 **Validación de Teléfono:** Integración de la API de Twilio para verificación vía SMS.
5. 🚀 **Despliegue a Producción:** Configuración del servidor web definitivo.

---
_Último commit registrado: `feat: Fase 1 - Seguridad Crítica implementada y probada` (01/07/2026 20:03:45)_