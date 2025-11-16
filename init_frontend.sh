#!/bin/bash
# Initialize SvelteKit frontend

echo "Creating frontend with SvelteKit..."
cd /Users/AshishR_T/Desktop/agoraHackNYU

# Create basic SvelteKit structure using npm create
npx --yes sv@latest create frontend --template minimal --types typescript --no-add-ons --no-install

echo "Frontend structure created!"
