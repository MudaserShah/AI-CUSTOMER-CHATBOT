<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Storefront conventions
- Keep the storefront catalog in a browser-safe data module, with local imported product media, so catalog content is reusable without server dependencies.
- The current store is a frontend catalog with an in-memory shopping bag; do not imply checkout is connected until a commerce provider is integrated.
- Define the monochrome store palette and reusable editorial styles in src/styles.css, so presentation remains consistent across store views.
