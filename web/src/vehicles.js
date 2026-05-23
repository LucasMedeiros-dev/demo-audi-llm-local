// Veículos em destaque no hero.
// Fotos reais de cada modelo Audi via Wikimedia Commons (Special:FilePath
// redireciona para o arquivo e aceita ?width=). URLs estáveis e validadas.
// Apenas vitrine visual — a cobertura real é validada no backend.
const COMMONS = "https://commons.wikimedia.org/wiki/Special:FilePath";
const photo = (file) => `${COMMONS}/${file}?width=800`;

export const FEATURED = [
  {
    nome: "Audi A4",
    anos: "2017–2025",
    desc: "Audi pre sense / frenagem automática (TSB 90).",
    img: photo("Audi_A4_B9_Limousine_3.0_TDI_quattro.JPG"),
  },
  {
    nome: "Audi RS5",
    anos: "2013 · 2018–2025",
    desc: "Ruído de freio dianteiro e pre sense.",
    img: photo("Audi_RS5_(ABA-8TCFSF)_front.JPG"),
  },
  {
    nome: "Audi Q5",
    anos: "2018–2025",
    desc: "Audi pre sense / frenagem automática (TSB 90).",
    img: photo("Audi_Q5_Facelift_S_line_2.0_TFSI_quattro_tiptronic_Daytonagrau.JPG"),
  },
  {
    nome: "Audi A6",
    anos: "2019–2025",
    desc: "Audi pre sense / frenagem automática (TSB 90).",
    img: photo("Audi_A6_C8_IMG_0081.jpg"),
  },
  {
    nome: "Audi Q7",
    anos: "2017–2025",
    desc: "Audi pre sense / frenagem automática (TSB 90).",
    img: photo("Audi_Q7_3.0_TDI_quattro_S_line.JPG"),
  },
  {
    nome: "Audi e-tron GT",
    anos: "2022–2025",
    desc: "Audi pre sense / frenagem automática (TSB 90).",
    img: photo("2021_Audi_e-tron_GT_-_front.jpg"),
  },
];
