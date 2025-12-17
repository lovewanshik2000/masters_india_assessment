#!/usr/bin/env python3
# Fix the broken Django template tag in usage_list.html

file_path = '/home/tspl/Documents/Kamlesh Lovewanshi/Learning/Django/test/templates/campaigns/usage_list.html'

with open(file_path, 'r') as f:
    lines = f.readlines()

# Fix lines 23-26 (0-indexed: 22-25)
# The broken template tag spans lines 24-25
fixed_lines = []
i = 0
while i < len(lines):
    if i == 23:  # Line 24 (0-indexed 23)
        # Check if this is the broken line
        if '{% if request.GET.campaign==campaign.id|stringformat:"s"' in lines[i]:
            # Replace with the fixed version on one line
            fixed_lines.append('                        <option value="{{ campaign.id }}" {% if request.GET.campaign == campaign.id|stringformat:"s" %}selected{% endif %}>\n')
            # Skip the next line (line 25) as it's part of the broken tag
            i += 2
            continue
    fixed_lines.append(lines[i])
    i += 1

with open(file_path, 'w') as f:
    f.writelines(fixed_lines)

print("Fixed the template syntax error in usage_list.html")
