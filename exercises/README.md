# Tiger Compiler Exercises

Interactive exercises and quizzes for learning compiler construction concepts.

## Available Exercises

### Activation Records Quiz (`ar.html`)
An interactive quiz covering:
- Stack frames and activation records
- Calling conventions
- Frame pointer vs stack pointer
- Static links and display
- Register allocation in procedure calls

## Deployment

The exercises are automatically deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow:

1. Triggers on pushes to `exercises/` directory
2. Creates an index page listing all exercises
3. Deploys to GitHub Pages

### Manual Deployment

You can also manually trigger the deployment from the GitHub Actions tab.

## Local Testing

Simply open any HTML file in your browser:
```bash
open exercises/ar.html
# or
python -m http.server 8000
# then visit http://localhost:8000/exercises/
```

## Adding New Exercises

1. Create a new HTML file in this directory
2. Update the index page in `.github/workflows/deploy-exercises.yml` to include the new exercise
3. Commit and push to deploy automatically



