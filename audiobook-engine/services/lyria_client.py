import os
from google import genai
from google.genai import types

def generate_music(prompt: str, output_path: str):
    print(f"Generating Lyria 3 Pro music for prompt: {prompt}")
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "lyria-3-pro-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
    )

    wrote_audio = False
    
    # Write chunks exactly into the final .wav file so it can be picked up by the Mixer
    with open(output_path, "wb") as f:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.parts is None:
                continue
                
            # If the chunk has audio bytes, stream them to disk
            if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
                f.write(chunk.parts[0].inline_data.data)
                wrote_audio = True
            else:
                try: 
                    if hasattr(chunk, 'text') and chunk.text:
                        print("Lyria Status:", chunk.text)
                except Exception: 
                    pass

    if not wrote_audio:
        raise Exception("Lyria API returned without any audio chunks. Ensure API key has sufficient paid quota.")
        
    print(f"Lyria file securely saved to: {output_path}")
    return output_path
