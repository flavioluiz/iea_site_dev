# Desenvolvimento local

```bash
git clone https://github.com/flavioluiz/iea_site_dev.git
cd iea_site_dev
python -m pip install -r scripts/requirements-cms.txt
hugo server -D
```

Antes de propor mudança técnica:

```bash
python scripts/validate_data.py
python scripts/security_check.py
hugo --gc --minify --printPathWarnings --environment production \
  --config config/_default/config.yaml,config/production/config.yaml
python scripts/check_links.py --public public \
  --base-url https://flavioluiz.github.io/iea_site/
```

Use Hugo Extended 0.152.2, a mesma versão fixada e verificada no CI.
