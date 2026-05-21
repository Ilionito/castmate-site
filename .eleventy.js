// ============================================================================
//  CastMate — Configuration Eleventy
//  Build : `npm run build` (sortie -> _site/)
//  Dev   : `npm start`     (live reload sur :8080)
// ============================================================================

module.exports = function (eleventyConfig) {
  // --- Assets statiques --------------------------------------------------
  // Copie texto les répertoires d'assets : images Framer, polices,
  // uploads CMS, et le loader Sveltia (/admin).
  eleventyConfig.addPassthroughCopy("src/assets");
  eleventyConfig.addPassthroughCopy("src/admin");

  // --- Pages Framer (passthrough temporaire) ----------------------------
  // Tant que les pages n'ont pas été converties en templates Nunjucks
  // (étape 2 du README-CMS.md), on les copie telles quelles.
  // Pour activer le templating sur la home : renommer src/index.html en
  // src/index.njk, remplacer les chaînes par {{ hero.title }} etc., et
  // SUPPRIMER la ligne addPassthroughCopy correspondante ci-dessous.
  eleventyConfig.addPassthroughCopy({ "src/index.html": "index.html" });
  eleventyConfig.addPassthroughCopy({ "src/contact": "contact" });
  eleventyConfig.addPassthroughCopy({ "src/demo": "demo" });
  eleventyConfig.addPassthroughCopy({ "src/legal": "legal" });

  return {
    dir: {
      input: "src",
      output: "_site",
      data: "_data",
      includes: "_includes",
    },
    // Seuls les .njk sont traités comme templates ; les .html restants
    // sont gérés par les passthrough copies ci-dessus.
    templateFormats: ["njk"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: "njk",
  };
};
