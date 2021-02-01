# Azure Communication Configuration for Python

> see https://aka.ms/autorest

### Setup
```ps
npm install -g autorest
```

### Generation
```ps
cd <swagger-folder>
autorest SWAGGER.md
```

### Settings
``` yaml
input-file: https://raw.githubusercontent.com/rikogeln/azure-rest-api-specs/5405e748f1c2bfb3fce42d18b3a532da52e2782f/specification/mixedreality/data-plane/Microsoft.MixedReality/preview/2021-01-01-preview/mr-arr.json
output-folder: ../azure/communication/chat/_generated
namespace: azure.communication.chat
no-namespace-folders: true
license-header: MICROSOFT_MIT_NO_VERSION
enable-xml: true
clear-output-folder: true
python: true
v3: true
no-async: false
add-credential: false
```
