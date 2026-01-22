// @ts-check

const { themes } = require("prism-react-renderer");
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Turbulence",
  tagline: "High-performance workflow simulation and testing framework",
  url: "https://farmanp.github.io",
  baseUrl: "/turbulence/docs/",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  favicon: "img/turbulence-logo.svg",

  organizationName: "farmanp",
  projectName: "turbulence",

  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          routeBasePath: "/"
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css")
        }
      }
    ]
  ],

  themeConfig: {
    navbar: {
      title: "Turbulence",
      logo: {
        alt: "Turbulence",
        src: "img/turbulence-logo.svg"
      },
      items: [
        {
          type: "doc",
          docId: "intro",
          position: "left",
          label: "Docs"
        }
      ]
    },
    prism: {
      theme: lightCodeTheme,
      darkTheme: darkCodeTheme
    }
  }
};

module.exports = config;
