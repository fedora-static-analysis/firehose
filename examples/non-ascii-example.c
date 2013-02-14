/* -*- coding: utf-8 -*- */
/*
    Copyright 2013 David Malcolm <dmalcolm@redhat.com>
    Copyright 2013 Red Hat, Inc.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301
    USA
*/
/*
  Example of a UTF-8-encoded source file containing non-ASCII characters

  U+2620 SKULL AND CROSSBONES: ☠

  Test of a Japanese unicode string: 文字化け
    (I believe this reads "mojibake", using 3 characters from the CJK
    Unified Ideographs area, followed by U+3051 HIRAGANA LETTER KE)

  Test of a character outside the BMP: 𝄡
    (this is U+1D121 MUSICAL SYMBOL C CLEF, which is encoded as:
      UTF-8: 0xF0 0x9D 0x84 0xA1 )

  Test of Unicode "Box Drawing" characters:
    ─ : U+2500 BOX DRAWINGS LIGHT HORIZONTAL
    │ : U+2502 BOX DRAWINGS LIGHT VERTICAL
    ┐ : U+2510 BOX DRAWINGS LIGHT DOWN AND LEFT
    └ : U+2514 BOX DRAWINGS LIGHT UP AND RIGHT
    ┘ : U+2518 BOX DRAWINGS LIGHT UP AND LEFT

        first ─> n0 ─> n1 ─> ... ─> nN ┐
          A                            │
          └────────────────────────────┘

  (the arrows are the greater than/less than and the letters A and V)
 */

int foo(int i, unsigned int j)
{
  if (i < j) {
    return 1;
  } else {
    return 0;
  }
}
