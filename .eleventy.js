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

  // --- Pages détachées du runtime Framer --------------------------------
  // Toutes les pages (home + sous-pages) sont en src/**/index.njk et
  // consomment src/_data. Aucun passthrough HTML : 11ty les rend toutes.

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
