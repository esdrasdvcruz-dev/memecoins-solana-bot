/**
 * Configuración central del negocio. Edita estos valores con tu información real:
 * nombre, horarios, dirección, redes sociales y textos de la página principal.
 */
export const businessConfig = {
  name: "ShakeandGo",
  tagline: "Alimentos y bebidas frescos, listos para recoger en tienda.",
  description:
    "Ordena en línea y recoge tu pedido en tienda. Aceptamos tarjeta, transferencia bancaria (nacional e internacional) y criptomonedas.",
  address: "Calz. de Tlalpan 5055, local 5, Tlalpan Centro II, Tlalpan, 14090 Ciudad de México, CDMX",
  phone: "+52 55 2173 7435",
  whatsapp: "+52 55 2173 7435",
  email: "contacto@shakeandgo.mx",
  hours: [
    { day: "Lunes a sábado", time: "8:00 am – 3:00 pm" },
    { day: "Domingo", time: "Cerrado" },
  ],
  // Aún sin confirmar: reemplaza con tus cuentas reales cuando las tengas.
  social: {
    instagram: "",
    facebook: "",
  },
  pickupIntervalMinutes: 15,
  pickupLeadTimeMinutes: 30,
};
