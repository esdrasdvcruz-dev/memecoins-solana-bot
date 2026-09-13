/**
 * Configuración central del negocio. Edita estos valores con tu información real:
 * nombre, horarios, dirección, redes sociales y textos de la página principal.
 */
export const businessConfig = {
  name: "Tu Negocio",
  tagline: "Alimentos y bebidas frescos, listos para recoger en tienda.",
  description:
    "Ordena en línea y recoge tu pedido en tienda. Aceptamos tarjeta, transferencia bancaria (nacional e internacional) y criptomonedas.",
  address: "Calle Ejemplo 123, Colonia Centro, Ciudad, México",
  phone: "+52 55 0000 0000",
  whatsapp: "+52 55 0000 0000",
  email: "contacto@tunegocio.com",
  hours: [
    { day: "Lunes a viernes", time: "9:00 am – 8:00 pm" },
    { day: "Sábado", time: "10:00 am – 6:00 pm" },
    { day: "Domingo", time: "Cerrado" },
  ],
  social: {
    instagram: "https://instagram.com/tunegocio",
    facebook: "https://facebook.com/tunegocio",
  },
  pickupIntervalMinutes: 15,
  pickupLeadTimeMinutes: 30,
};
