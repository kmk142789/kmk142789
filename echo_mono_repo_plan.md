# echo-mono-repo / EchoCore-mono setup plan

This environment cannot create a new GitHub repository or push content because no GitHub credentials or API tokens are available. To finish the request when you have GitHub access:

1. Create a new empty GitHub repository named either `echo-mono-repo` or `EchoCore-mono`.
2. From your local checkout of this project, copy only the AI Studio root files into a clean directory:
   - `App.tsx`
   - `index.tsx`
   - `index.html`
   - `metadata.json`
   - `types.ts`
   - `services/geminiService.ts`
   - `components/Terminal.tsx`
   - `components/StatusDisplay.tsx`
   - `components/MythWeaver.tsx`
3. Initialize Git in that directory, add the files, and push the initial commit to the new GitHub repository using your credentials.

Once the repository exists on GitHub, the `read_github_file` tool will operate against it.
