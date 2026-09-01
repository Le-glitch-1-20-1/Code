#version 330

in vec2 fragTexCoord;
out vec4 finalColor;

uniform sampler2D texture0;
uniform vec2 direction;
uniform vec2 resolution;

void main()
{
	vec4 color = vec4(0.0);
	vec2 off1 = vec2(1.3846153846) * direction / resolution;
	vec2 off2 = vec2(3.2307692308) * direction / resolution;

	color += texture(texture0, fragTexCoord) * 0.2270270270;
	color += texture(texture0, fragTexCoord + off1) * 0.3162162162;
	color += texture(texture0, fragTexCoord - off1) * 0.3162162162;
	color += texture(texture0, fragTexCoord + off2) * 0.0702702703;
	color += texture(texture0, fragTexCoord - off2) * 0.0702702703;

	finalColor = color;
}
