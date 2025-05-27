# BBC Bot

[BBC Bot](https://github.com/ttaayyllaarr/bbc_bot) is an automated bot designed to run on an AWS instance. This repository contains the bot’s source code and deployment scripts to help you run and manage it efficiently using GitHub Actions.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
  - [Environment Variables and Secrets](#environment-variables-and-secrets)
  - [SSH Key for Deployment](#ssh-key-for-deployment)
- [Deployment](#deployment)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Overview

BBC Bot is built for automated tasks on your AWS EC2 instance. In our current setup, changes pushed to the repository are deployed automatically via GitHub Actions. The deployment pipeline uses secure SSH connectivity (powered by [appleboy/ssh-action](https://github.com/appleboy/ssh-action)) to pull the latest changes on your AWS instance and restart the bot using PM2.

This bot can be used as-is or extended to power additional features (like notifications, data processing, or even a Discord bot) based on your requirements.

---

## Features

- **Automated Deployment:**  
  Push your changes to the main branch and let GitHub Actions handle the deployment.
- **Secure Integration:**  
  Uses environment secrets and SSH keys to securely deploy your bot.
- **Node/PM2 Process Management:**  
  Easily manage the running process via PM2 (or modify to use your preferred process manager).
- **Customizable:**  
  Extend or modify bot features as needed.

---

## Setup and Installation

### Local Development

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ttaayyllaarr/bbc_bot.git
   cd bbc_bot
