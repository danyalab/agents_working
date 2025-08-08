%%bash  
export PROJECT\_ID="" \#@param {type:"string"}  
export PROJECT\_NUMBER="" \#@param {type:"string"}  
export REASONING\_ENGINE="projects//locations/us-central1/reasoningEngines/" \#@param {type:"string"}  
export AGENT\_DISPLAY\_NAME=""  
export AGENT\_DESCRIPTION=""  
export AGENT\_ID="" \#@param {type:"string"}  
export AS\_APP="enterprise-search-" \#@param {type:"string"}  
\# export AS\_APP="agentspace-"  
curl \-X PATCH \-H "Authorization: Bearer $(gcloud auth print-access-token)" \\  
\-H "Content-Type: application/json" \\  
\-H "x-goog-user-project: ${PROJECT\_ID}" \\  
https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT\_NUMBER}/locations/global/collections/default\_collection/engines/${AS\_APP}/assistants/default\_assistant?updateMask=agent\_configs \-d '{  
    "name": "projects/${PROJECT\_NUMBER}/locations/global/collections/default\_collection/engines/${AS\_APP}/assistants/default\_assistant",  
    "displayName": "Default Assistant",  
    "agentConfigs": \[{  
      "displayName": "'"${AGENT\_DISPLAY\_NAME}"'",  
      "vertexAiSdkAgentConnectionInfo": {  
        "reasoningEngine": "'"${REASONING\_ENGINE}"'"  
      },  
      "toolDescription": "'"${AGENT\_DESCRIPTION}"'",  
      "icon": {  
        "uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/corporate\_fare/default/24px.svg"  
      },  
      "id": "'"${AGENT\_ID}"'"  
    }\]  
  }'  
