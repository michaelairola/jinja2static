# Jinja2Static

A lightweight, zero-config static site generator powered by Jinja2 templating. Build fast, modern static websites without the complexity of heavier frameworks.

## Overview

Jinja2Static transforms Jinja2 templates into static HTML files. It's designed to be simple, straightforward, and efficient—perfect for blogs, portfolios, documentation, and any static site project where you want the power of templating without bloat.

## Features

- **Jinja2 Templating**: Use the full power of Jinja2 templates to build your site
- **Asset Management**: Automatically copy CSS, JavaScript, images, and other assets to your output directory
- **Development Server**: Built-in hot reload server for rapid development (`jinja2static serve`)
- **File Watching**: Watch for changes and rebuild automatically (`jinja2static watch`)
- **YAML Configuration**: Simple, declarative project configuration
- **Minimal Dependencies**: Only requires Jinja2, PyYAML, and watchfiles

## Quick Start

### Installation

```bash
pip install jinja2static
```

### Initialize a Project

```bash
jinja2static init my-site
cd my-site
```

This creates a basic project structure with templates and assets directories.

### Build Your Site

```bash
jinja2static build
```

Your static site will be generated in the `dist/` directory.

### Development Workflow

Watch for changes and rebuild automatically:
```bash
jinja2static watch
```

Or run a local development server with hot reload:
```bash
jinja2static serve
```

*OR* do both at the same time!
```bash
jinja2static dev
```

## Project Structure

A typical Jinja2Static project looks like this:

```
my-site/
├── pyproject.toml       # Project configuration
├── templates/              # Your Jinja2 templates
│   └── index.html
├── assets/                 # Static assets (CSS, JS, images, etc.)
│   └── style.css
└── data/                   # (Optional) Data files in YAML format
    └── config.yml
```

## Configuration

Configuration is managed through `pyproject.toml`:

```toml
[tools.jinja2static]
templates_dir = "templates"
assets_dir = "assets"
output_dir = "dist"
data_dir = "data"
```

## Use Cases

- **Personal Blogs**: Simple, fast blogs with Jinja2 templating
- **Portfolio Sites**: Showcase your work without complex tooling
- **Documentation Sites**: Generate docs from templates and data files
- **Landing Pages**: Quick static sites with reusable components
- **Resume Sites**: Dynamic resume generation from data files

## License

MIT
