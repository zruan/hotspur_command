# config.py can include title and subfolder descripitons that are displayed in the dashboard
# Use sqlite instead of json file as metadata storage
    - Allow simultaneous writing and reading by web application
    - Allow async stepwise download of data
# Parse gAutomatch
# Canvas renderer over micrograph image to:
    - Show picks
    - Show scalebar
# Allow user to annotate
    - Categroize micrgropahs (Bad/good/refit ctf)
    - Edit picks
    - Annotate grid conditions
# Processor should be more tolerant for erros
    - Keep log in file
    - Have sperate log with failed files
# Have tools to restart processing for images
    - Parser should be only process to edite data.json (might not be true if using sqlite)
    - Delete lockfiles
# Write tool to generate particle stack for project (ideally end project is relion project with imported particles)