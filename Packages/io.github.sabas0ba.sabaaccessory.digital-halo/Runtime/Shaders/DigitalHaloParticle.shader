Shader "SabaAccessory/Digital Halo Particle"
{
    Properties
    {
        [HDR] _Color ("Particle Color", Color) = (1.2, 1.2, 1.2, 1)
        _Emission ("Emission", Range(0, 4)) = 0.55
        _Opacity ("Opacity", Range(0, 1)) = 0.42
    }

    SubShader
    {
        Tags
        {
            "Queue" = "Transparent+1"
            "RenderType" = "Transparent"
            "IgnoreProjector" = "True"
            "VRCFallback" = "UnlitTransparent"
        }

        Pass
        {
            Blend SrcAlpha One
            Cull Off
            ZWrite Off

            CGPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            float4 _Color;
            float _Emission;
            float _Opacity;

            struct appdata
            {
                float4 vertex : POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                float4 color : COLOR;
                float2 uv : TEXCOORD0;
            };

            v2f vert(appdata input)
            {
                v2f output;
                output.position = UnityObjectToClipPos(input.vertex);
                output.color = input.color;
                output.uv = input.uv;
                return output;
            }

            float4 frag(v2f input) : SV_Target
            {
                float2 distanceToEdge = min(input.uv, 1.0 - input.uv);
                float rectangle = step(0.08, min(distanceToEdge.x, distanceToEdge.y));
                float alpha = input.color.a * _Opacity * rectangle;
                return float4(_Color.rgb * input.color.rgb * _Emission, alpha);
            }
            ENDCG
        }
    }

    Fallback "Unlit/Transparent"
}
