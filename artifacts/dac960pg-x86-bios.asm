
bios.rom:     file format binary


Disassembly of section .data:

00000000 <.data>:
       0:	55                   	push   %bp
       1:	aa                   	stos   %al,%es:(%di)
       2:	38 e9                	cmp    %ch,%cl
       4:	fa                   	cli    
       5:	2f                   	das    
	...
      16:	00 00                	add    %al,(%bx,%si)
      18:	28 00                	sub    %al,(%bx,%si)
      1a:	00 00                	add    %al,(%bx,%si)
      1c:	00 00                	add    %al,(%bx,%si)
      1e:	00 00                	add    %al,(%bx,%si)
      20:	fe                   	(bad)  
      21:	3f                   	aas    
      22:	00 eb                	add    %ch,%bl
      24:	00 fc                	add    %bh,%ah
      26:	00 41 50             	add    %al,0x50(%bx,%di)
      29:	43                   	inc    %bx
      2a:	49                   	dec    %cx
      2b:	52                   	push   %dx
      2c:	69 10 10 00          	imul   $0x10,(%bx,%si),%dx
      30:	00 00                	add    %al,(%bx,%si)
      32:	18 00                	sbb    %al,(%bx,%si)
      34:	00 00                	add    %al,(%bx,%si)
      36:	04 01                	add    $0x1,%al
      38:	38 00                	cmp    %al,(%bx,%si)
      3a:	0a 04                	or     (%si),%al
      3c:	00 80 00 00          	add    %al,0x0(%bx,%si)
      40:	ff                   	(bad)  
      41:	ff                   	(bad)  
      42:	ff                   	(bad)  
      43:	ff                   	(bad)  
      44:	ff                   	(bad)  
      45:	ff                   	(bad)  
      46:	ff                   	(bad)  
      47:	ff                   	(bad)  
      48:	ff                   	(bad)  
      49:	ff                   	(bad)  
      4a:	ff                   	(bad)  
      4b:	ff                   	(bad)  
      4c:	ff                   	(bad)  
      4d:	ff                   	(bad)  
      4e:	ff                   	(bad)  
      4f:	ff                   	(bad)  
      50:	ff                   	(bad)  
      51:	ff                   	(bad)  
      52:	ff                   	(bad)  
      53:	ff                   	(bad)  
      54:	ff                   	(bad)  
      55:	ff                   	(bad)  
      56:	ff                   	(bad)  
      57:	ff                   	(bad)  
      58:	ff                   	(bad)  
      59:	ff                   	(bad)  
      5a:	ff                   	(bad)  
      5b:	ff                   	(bad)  
      5c:	ff                   	(bad)  
      5d:	ff                   	(bad)  
      5e:	ff                   	(bad)  
      5f:	ff                   	(bad)  
      60:	ff                   	(bad)  
      61:	ff                   	(bad)  
      62:	ff                   	(bad)  
      63:	ff                   	(bad)  
      64:	ff                   	(bad)  
      65:	ff                   	(bad)  
      66:	ff                   	(bad)  
      67:	ff                   	(bad)  
      68:	ff                   	(bad)  
      69:	ff                   	(bad)  
      6a:	ff                   	(bad)  
      6b:	ff                   	(bad)  
      6c:	ff                   	(bad)  
      6d:	ff                   	(bad)  
      6e:	ff                   	(bad)  
      6f:	ff                   	(bad)  
      70:	ff                   	(bad)  
      71:	ff                   	(bad)  
      72:	ff                   	(bad)  
      73:	ff                   	(bad)  
      74:	ff                   	(bad)  
      75:	ff                   	(bad)  
      76:	ff                   	(bad)  
      77:	ff                   	(bad)  
      78:	ff                   	(bad)  
      79:	ff                   	(bad)  
      7a:	ff                   	(bad)  
      7b:	ff                   	(bad)  
      7c:	ff                   	(bad)  
      7d:	ff                   	(bad)  
      7e:	ff                   	(bad)  
      7f:	ff 22                	jmp    *(%bp,%si)
      81:	22 22                	and    (%bp,%si),%ah
      83:	22 22                	and    (%bp,%si),%ah
      85:	22 22                	and    (%bp,%si),%ah
      87:	4d                   	dec    %bp
      88:	79 6c                	jns    0xf6
      8a:	65 78 20             	gs js  0xad
      8d:	43                   	inc    %bx
      8e:	6f                   	outsw  %ds:(%si),(%dx)
      8f:	72 70                	jb     0x101
      91:	6f                   	outsw  %ds:(%si),(%dx)
      92:	72 61                	jb     0xf5
      94:	74 69                	je     0xff
      96:	6f                   	outsw  %ds:(%si),(%dx)
      97:	6e                   	outsb  %ds:(%si),(%dx)
      98:	28 63 29             	sub    %ah,0x29(%bp,%di)
      9b:	22 22                	and    (%bp,%si),%ah
      9d:	22 22                	and    (%bp,%si),%ah
      9f:	22 ff                	and    %bh,%bh
      a1:	ff                   	(bad)  
      a2:	ff                   	(bad)  
      a3:	ff                   	(bad)  
      a4:	ff                   	(bad)  
      a5:	ff                   	(bad)  
      a6:	ff                   	(bad)  
      a7:	ff                   	(bad)  
      a8:	ff                   	(bad)  
      a9:	ff                   	(bad)  
      aa:	ff                   	(bad)  
      ab:	ff                   	(bad)  
      ac:	ff                   	(bad)  
      ad:	ff                   	(bad)  
      ae:	ff                   	(bad)  
      af:	ff                   	(bad)  
      b0:	ff                   	(bad)  
      b1:	ff                   	(bad)  
      b2:	ff                   	(bad)  
      b3:	ff                   	(bad)  
      b4:	ff                   	(bad)  
      b5:	ff                   	(bad)  
      b6:	ff                   	(bad)  
      b7:	ff                   	(bad)  
      b8:	ff                   	(bad)  
      b9:	ff                   	(bad)  
      ba:	ff                   	(bad)  
      bb:	ff                   	(bad)  
      bc:	ff                   	(bad)  
      bd:	ff                   	(bad)  
      be:	ff                   	(bad)  
      bf:	ff                   	(bad)  
      c0:	ff                   	(bad)  
      c1:	ff                   	(bad)  
      c2:	ff                   	(bad)  
      c3:	ff                   	(bad)  
      c4:	ff                   	(bad)  
      c5:	ff                   	(bad)  
      c6:	ff                   	(bad)  
      c7:	ff                   	(bad)  
      c8:	ff                   	(bad)  
      c9:	ff                   	(bad)  
      ca:	ff                   	(bad)  
      cb:	ff                   	(bad)  
      cc:	ff                   	(bad)  
      cd:	ff                   	(bad)  
      ce:	ff                   	(bad)  
      cf:	ff                   	(bad)  
      d0:	ff                   	(bad)  
      d1:	ff                   	(bad)  
      d2:	ff                   	(bad)  
      d3:	ff                   	(bad)  
      d4:	ff                   	(bad)  
      d5:	ff                   	(bad)  
      d6:	ff                   	(bad)  
      d7:	ff                   	(bad)  
      d8:	ff                   	(bad)  
      d9:	ff                   	(bad)  
      da:	ff                   	(bad)  
      db:	ff                   	(bad)  
      dc:	ff                   	(bad)  
      dd:	ff                   	(bad)  
      de:	ff                   	(bad)  
      df:	ff                   	(bad)  
      e0:	ff                   	(bad)  
      e1:	ff                   	(bad)  
      e2:	ff                   	(bad)  
      e3:	ff                   	(bad)  
      e4:	ff                   	(bad)  
      e5:	ff                   	(bad)  
      e6:	ff                   	(bad)  
      e7:	ff                   	(bad)  
      e8:	ff                   	(bad)  
      e9:	ff                   	(bad)  
      ea:	ff                   	(bad)  
      eb:	ff                   	(bad)  
      ec:	ff                   	(bad)  
      ed:	ff                   	(bad)  
      ee:	ff                   	(bad)  
      ef:	ff                   	(bad)  
      f0:	ff                   	(bad)  
      f1:	ff                   	(bad)  
      f2:	ff                   	(bad)  
      f3:	ff                   	(bad)  
      f4:	ff                   	(bad)  
      f5:	ff                   	(bad)  
      f6:	ff                   	(bad)  
      f7:	ff                   	(bad)  
      f8:	ff                   	(bad)  
      f9:	ff                   	(bad)  
      fa:	ff                   	(bad)  
      fb:	ff                   	(bad)  
      fc:	ff                   	(bad)  
      fd:	ff                   	(bad)  
      fe:	ff                   	(bad)  
      ff:	ff                   	(bad)  
     100:	ff                   	(bad)  
     101:	ff                   	(bad)  
     102:	ff                   	(bad)  
     103:	ff                   	(bad)  
     104:	ff                   	(bad)  
     105:	ff                   	(bad)  
     106:	ff                   	(bad)  
     107:	ff                   	(bad)  
     108:	ff                   	(bad)  
     109:	ff                   	(bad)  
     10a:	ff                   	(bad)  
     10b:	ff                   	(bad)  
     10c:	ff                   	(bad)  
     10d:	ff                   	(bad)  
     10e:	ff                   	(bad)  
     10f:	ff                   	(bad)  
     110:	ff                   	(bad)  
     111:	ff                   	(bad)  
     112:	ff                   	(bad)  
     113:	ff                   	(bad)  
     114:	ff                   	(bad)  
     115:	ff                   	(bad)  
     116:	ff                   	(bad)  
     117:	ff                   	(bad)  
     118:	ff                   	(bad)  
     119:	ff                   	(bad)  
     11a:	ff                   	(bad)  
     11b:	ff                   	(bad)  
     11c:	ff                   	(bad)  
     11d:	ff                   	(bad)  
     11e:	ff                   	(bad)  
     11f:	ff                   	(bad)  
     120:	ff                   	(bad)  
     121:	ff                   	(bad)  
     122:	ff                   	(bad)  
     123:	ff                   	(bad)  
     124:	ff                   	(bad)  
     125:	ff                   	(bad)  
     126:	ff                   	(bad)  
     127:	ff                   	(bad)  
     128:	ff                   	(bad)  
     129:	ff                   	(bad)  
     12a:	ff                   	(bad)  
     12b:	ff                   	(bad)  
     12c:	ff                   	(bad)  
     12d:	ff                   	(bad)  
     12e:	ff                   	(bad)  
     12f:	ff                   	(bad)  
     130:	ff                   	(bad)  
     131:	ff                   	(bad)  
     132:	ff                   	(bad)  
     133:	ff                   	(bad)  
     134:	ff                   	(bad)  
     135:	ff                   	(bad)  
     136:	ff                   	(bad)  
     137:	ff                   	(bad)  
     138:	ff                   	(bad)  
     139:	ff                   	(bad)  
     13a:	ff                   	(bad)  
     13b:	ff                   	(bad)  
     13c:	ff                   	(bad)  
     13d:	ff                   	(bad)  
     13e:	ff                   	(bad)  
     13f:	ff                   	(bad)  
     140:	ff                   	(bad)  
     141:	ff                   	(bad)  
     142:	ff                   	(bad)  
     143:	ff                   	(bad)  
     144:	ff                   	(bad)  
     145:	ff                   	(bad)  
     146:	ff                   	(bad)  
     147:	ff                   	(bad)  
     148:	ff                   	(bad)  
     149:	ff                   	(bad)  
     14a:	ff                   	(bad)  
     14b:	ff                   	(bad)  
     14c:	ff                   	(bad)  
     14d:	ff                   	(bad)  
     14e:	ff                   	(bad)  
     14f:	ff 00                	incw   (%bx,%si)
	...
     15d:	00 00                	add    %al,(%bx,%si)
     15f:	00 4b 6c             	add    %cl,0x6c(%bp,%di)
     162:	53                   	push   %bx
     163:	68 04 0a             	push   $0xa04
     166:	00 07                	add    %al,(%bx)
     168:	02 02                	add    (%bp,%si),%al
     16a:	13 63 29             	adc    0x29(%bp,%di),%sp
     16d:	00 0b                	add    %cl,(%bp,%di)
     16f:	00 34                	add    %dh,(%si)
     171:	2e 31 30             	xor    %si,%cs:(%bx,%si)
     174:	2d 34 31             	sub    $0x3134,%ax
     177:	20 20                	and    %ah,(%bx,%si)
     179:	6b 61 69 20          	imul   $0x20,0x69(%bx,%di),%sp
     17d:	30 32                	xor    %dh,(%bp,%si)
     17f:	2c 20                	sub    $0x20,%al
     181:	31 39                	xor    %di,(%bx,%di)
     183:	39 39                	cmp    %di,(%bx,%di)
     185:	29 00                	sub    %ax,(%bx,%si)
	...
     1af:	00 55 55             	add    %dl,0x55(%di)
     1b2:	55                   	push   %bp
     1b3:	55                   	push   %bp
     1b4:	55                   	push   %bp
     1b5:	55                   	push   %bp
     1b6:	55                   	push   %bp
     1b7:	55                   	push   %bp
     1b8:	55                   	push   %bp
     1b9:	55                   	push   %bp
     1ba:	55                   	push   %bp
     1bb:	55                   	push   %bp
     1bc:	55                   	push   %bp
     1bd:	55                   	push   %bp
     1be:	55                   	push   %bp
     1bf:	55                   	push   %bp
     1c0:	55                   	push   %bp
     1c1:	55                   	push   %bp
     1c2:	55                   	push   %bp
     1c3:	55                   	push   %bp
     1c4:	55                   	push   %bp
     1c5:	55                   	push   %bp
     1c6:	55                   	push   %bp
     1c7:	55                   	push   %bp
     1c8:	55                   	push   %bp
     1c9:	55                   	push   %bp
     1ca:	55                   	push   %bp
     1cb:	55                   	push   %bp
     1cc:	55                   	push   %bp
     1cd:	55                   	push   %bp
     1ce:	55                   	push   %bp
     1cf:	55                   	push   %bp
     1d0:	55                   	push   %bp
     1d1:	55                   	push   %bp
     1d2:	55                   	push   %bp
     1d3:	55                   	push   %bp
     1d4:	55                   	push   %bp
     1d5:	55                   	push   %bp
     1d6:	55                   	push   %bp
     1d7:	55                   	push   %bp
     1d8:	55                   	push   %bp
     1d9:	55                   	push   %bp
     1da:	55                   	push   %bp
     1db:	55                   	push   %bp
     1dc:	55                   	push   %bp
     1dd:	55                   	push   %bp
     1de:	55                   	push   %bp
     1df:	55                   	push   %bp
     1e0:	55                   	push   %bp
     1e1:	55                   	push   %bp
     1e2:	55                   	push   %bp
     1e3:	55                   	push   %bp
     1e4:	55                   	push   %bp
     1e5:	55                   	push   %bp
     1e6:	55                   	push   %bp
     1e7:	55                   	push   %bp
     1e8:	55                   	push   %bp
     1e9:	55                   	push   %bp
     1ea:	55                   	push   %bp
     1eb:	55                   	push   %bp
     1ec:	55                   	push   %bp
     1ed:	55                   	push   %bp
     1ee:	55                   	push   %bp
     1ef:	55                   	push   %bp
     1f0:	55                   	push   %bp
     1f1:	55                   	push   %bp
     1f2:	55                   	push   %bp
     1f3:	55                   	push   %bp
     1f4:	55                   	push   %bp
     1f5:	55                   	push   %bp
     1f6:	55                   	push   %bp
     1f7:	55                   	push   %bp
     1f8:	55                   	push   %bp
     1f9:	55                   	push   %bp
     1fa:	55                   	push   %bp
     1fb:	55                   	push   %bp
     1fc:	55                   	push   %bp
     1fd:	55                   	push   %bp
     1fe:	55                   	push   %bp
     1ff:	55                   	push   %bp
     200:	3d 00 bf             	cmp    $0xbf00,%ax
     203:	75 05                	jne    0x20a
     205:	83 ff 00             	cmp    $0x0,%di
     208:	74 73                	je     0x27d
     20a:	80 fa 8f             	cmp    $0x8f,%dl
     20d:	75 15                	jne    0x224
     20f:	80 fc fe             	cmp    $0xfe,%ah
     212:	0f 84 c2 00          	je     0x2d8
     216:	80 fc fd             	cmp    $0xfd,%ah
     219:	0f 84 bb 00          	je     0x2d8
     21d:	80 fc ff             	cmp    $0xff,%ah
     220:	0f 84 c8 01          	je     0x3ec
     224:	2e f6 06 56 01 01    	testb  $0x1,%cs:0x156
     22a:	0f 85 26 01          	jne    0x354
     22e:	80 fa 80             	cmp    $0x80,%dl
     231:	0f 82 d0 00          	jb     0x305
     235:	52                   	push   %dx
     236:	80 e2 7f             	and    $0x7f,%dl
     239:	2e 3a 16 d0 00       	cmp    %cs:0xd0,%dl
     23e:	72 26                	jb     0x266
     240:	2e 8a 36 d0 00       	mov    %cs:0xd0,%dh
     245:	2e 02 36 57 01       	add    %cs:0x157,%dh
     24a:	38 f2                	cmp    %dh,%dl
     24c:	0f 82 9b 01          	jb     0x3eb
     250:	2e 80 3e e3 1b 00    	cmpb   $0x0,%cs:0x1be3
     256:	74 0e                	je     0x266
     258:	2e 8a 36 e7 1b       	mov    %cs:0x1be7,%dh
     25d:	80 e6 7f             	and    $0x7f,%dh
     260:	38 f2                	cmp    %dh,%dl
     262:	0f 84 85 01          	je     0x3eb
     266:	2e 80 3e e4 1b 00    	cmpb   $0x0,%cs:0x1be4
     26c:	0f 85 aa 00          	jne    0x31a
     270:	5a                   	pop    %dx
     271:	0a e4                	or     %ah,%ah
     273:	0f 85 dd 00          	jne    0x354
     277:	e8 9f 0a             	call   0xd19
     27a:	ca 02 00             	lret   $0x2
     27d:	66 60                	pushal 
     27f:	0f a8                	push   %gs
     281:	0f a0                	push   %fs
     283:	06                   	push   %es
     284:	1e                   	push   %ds
     285:	0e                   	push   %cs
     286:	1f                   	pop    %ds
     287:	0f b6 0e 55 01       	movzbw 0x155,%cx
     28c:	33 f6                	xor    %si,%si
     28e:	3b 9c a0 00          	cmp    0xa0(%si),%bx
     292:	74 12                	je     0x2a6
     294:	83 c6 02             	add    $0x2,%si
     297:	e2 f5                	loop   0x28e
     299:	1f                   	pop    %ds
     29a:	07                   	pop    %es
     29b:	0f a1                	pop    %fs
     29d:	0f a9                	pop    %gs
     29f:	66 61                	popal  
     2a1:	2e ff 2e 50 01       	ljmp   *%cs:0x150
     2a6:	56                   	push   %si
     2a7:	bf 10 00             	mov    $0x10,%di
     2aa:	b8 0a b1             	mov    $0xb10a,%ax
     2ad:	cd 1a                	int    $0x1a
     2af:	5e                   	pop    %si
     2b0:	72 18                	jb     0x2ca
     2b2:	d1 e6                	shl    %si
     2b4:	66 83 e1 f0          	and    $0xfffffff0,%ecx
     2b8:	66 89 8c 10 01       	mov    %ecx,0x110(%si)
     2bd:	1f                   	pop    %ds
     2be:	07                   	pop    %es
     2bf:	0f a1                	pop    %fs
     2c1:	0f a9                	pop    %gs
     2c3:	66 61                	popal  
     2c5:	32 e4                	xor    %ah,%ah
     2c7:	ca 02 00             	lret   $0x2
     2ca:	1f                   	pop    %ds
     2cb:	07                   	pop    %es
     2cc:	0f a1                	pop    %fs
     2ce:	0f a9                	pop    %gs
     2d0:	66 61                	popal  
     2d2:	b4 01                	mov    $0x1,%ah
     2d4:	f9                   	stc    
     2d5:	ca 02 00             	lret   $0x2
     2d8:	53                   	push   %bx
     2d9:	1e                   	push   %ds
     2da:	8e db                	mov    %bx,%ds
     2dc:	8b d9                	mov    %cx,%bx
     2de:	8a 1f                	mov    (%bx),%bl
     2e0:	2e 3a 1e 54 01       	cmp    %cs:0x154,%bl
     2e5:	1f                   	pop    %ds
     2e6:	5b                   	pop    %bx
     2e7:	0f 83 01 01          	jae    0x3ec
     2eb:	2e ff 2e 50 01       	ljmp   *%cs:0x150
     2f0:	2e 80 3e e4 1b 00    	cmpb   $0x0,%cs:0x1be4
     2f6:	74 08                	je     0x300
     2f8:	2e 80 3e e7 1b 00    	cmpb   $0x0,%cs:0x1be7
     2fe:	74 2f                	je     0x32f
     300:	2e ff 2e 58 01       	ljmp   *%cs:0x158
     305:	2e 80 3e e4 1b 00    	cmpb   $0x0,%cs:0x1be4
     30b:	74 08                	je     0x315
     30d:	2e 80 3e e7 1b 00    	cmpb   $0x0,%cs:0x1be7
     313:	74 1a                	je     0x32f
     315:	2e ff 2e 50 01       	ljmp   *%cs:0x150
     31a:	0a d2                	or     %dl,%dl
     31c:	0f 84 cb 00          	je     0x3eb
     320:	5a                   	pop    %dx
     321:	0a e4                	or     %ah,%ah
     323:	75 16                	jne    0x33b
     325:	52                   	push   %dx
     326:	fe ca                	dec    %dl
     328:	e8 ee 09             	call   0xd19
     32b:	5a                   	pop    %dx
     32c:	ca 02 00             	lret   $0x2
     32f:	80 fa 00             	cmp    $0x0,%dl
     332:	0f 84 b6 00          	je     0x3ec
     336:	80 fc 15             	cmp    $0x15,%ah
     339:	74 0a                	je     0x345
     33b:	80 fc 08             	cmp    $0x8,%ah
     33e:	74 12                	je     0x352
     340:	80 fc 15             	cmp    $0x15,%ah
     343:	74 0d                	je     0x352
     345:	52                   	push   %dx
     346:	fe ca                	dec    %dl
     348:	9c                   	pushf  
     349:	2e ff 1e 50 01       	lcall  *%cs:0x150
     34e:	5a                   	pop    %dx
     34f:	ca 02 00             	lret   $0x2
     352:	fe ca                	dec    %dl
     354:	2e ff 2e 50 01       	ljmp   *%cs:0x150
     359:	2e 80 3e e1 1b 00    	cmpb   $0x0,%cs:0x1be1
     35f:	75 08                	jne    0x369
     361:	2e 80 3e e3 1b 00    	cmpb   $0x0,%cs:0x1be3
     367:	74 7d                	je     0x3e6
     369:	66 60                	pushal 
     36b:	0f a8                	push   %gs
     36d:	0f a0                	push   %fs
     36f:	06                   	push   %es
     370:	1e                   	push   %ds
     371:	0e                   	push   %cs
     372:	1f                   	pop    %ds
     373:	2e a1 fe 1b          	mov    %cs:0x1bfe,%ax
     377:	2e 8e 06 00 1c       	mov    %cs:0x1c00,%es
     37c:	26 03 06 0e 00       	add    %es:0xe,%ax
     381:	8e c0                	mov    %ax,%es
     383:	66 33 ed             	xor    %ebp,%ebp
     386:	0f 20 c0             	mov    %cr0,%eax
     389:	66 26 89 86 ec 02    	mov    %eax,%es:0x2ec(%bp)
     38f:	e8 f6 0e             	call   0x1288
     392:	e8 62 0e             	call   0x11f7
     395:	2e 80 3e e1 1b 00    	cmpb   $0x0,%cs:0x1be1
     39b:	74 03                	je     0x3a0
     39d:	e8 0c 0b             	call   0xeac
     3a0:	a0 e6 1b             	mov    0x1be6,%al
     3a3:	26 88 86 e2 02       	mov    %al,%es:0x2e2(%bp)
     3a8:	66 0f b7 06 fc 1b    	movzwl 0x1bfc,%eax
     3ae:	66 26 89 86 f4 02    	mov    %eax,%es:0x2f4(%bp)
     3b4:	66 a1 08 1c          	mov    0x1c08,%eax
     3b8:	66 26 89 86 f8 02    	mov    %eax,%es:0x2f8(%bp)
     3be:	66 a1 0c 1c          	mov    0x1c0c,%eax
     3c2:	66 26 89 86 f0 02    	mov    %eax,%es:0x2f0(%bp)
     3c8:	26 c6 86 e8 02 00    	movb   $0x0,%es:0x2e8(%bp)
     3ce:	e8 17 07             	call   0xae8
     3d1:	1f                   	pop    %ds
     3d2:	07                   	pop    %es
     3d3:	0f a1                	pop    %fs
     3d5:	0f a9                	pop    %gs
     3d7:	66 61                	popal  
     3d9:	75 0b                	jne    0x3e6
     3db:	2e 0f b6 16 e7 1b    	movzbw %cs:0x1be7,%dx
     3e1:	2e ff 2e 08 1c       	ljmp   *%cs:0x1c08
     3e6:	2e ff 2e 5c 01       	ljmp   *%cs:0x15c
     3eb:	5a                   	pop    %dx
     3ec:	66 55                	push   %ebp
     3ee:	66 50                	push   %eax
     3f0:	06                   	push   %es
     3f1:	2e a1 fe 1b          	mov    %cs:0x1bfe,%ax
     3f5:	2e 8e 06 00 1c       	mov    %cs:0x1c00,%es
     3fa:	26 03 06 0e 00       	add    %es:0xe,%ax
     3ff:	8e c0                	mov    %ax,%es
     401:	66 33 ed             	xor    %ebp,%ebp
     404:	26 8f 86 ca 02       	pop    %es:0x2ca(%bp)
     409:	66 26 8f 86 b0 02    	popl   %es:0x2b0(%bp)
     40f:	26 8c 9e c8 02       	mov    %ds,%es:0x2c8(%bp)
     414:	26 8c ae cc 02       	mov    %gs,%es:0x2cc(%bp)
     419:	26 8c a6 ce 02       	mov    %fs,%es:0x2ce(%bp)
     41e:	66 26 89 9e b4 02    	mov    %ebx,%es:0x2b4(%bp)
     424:	66 26 89 8e b8 02    	mov    %ecx,%es:0x2b8(%bp)
     42a:	66 26 89 96 bc 02    	mov    %edx,%es:0x2bc(%bp)
     430:	66 26 89 b6 c4 02    	mov    %esi,%es:0x2c4(%bp)
     436:	66 26 89 be c0 02    	mov    %edi,%es:0x2c0(%bp)
     43c:	0e                   	push   %cs
     43d:	1f                   	pop    %ds
     43e:	e8 c9 0e             	call   0x130a
     441:	8e 26 00 1c          	mov    0x1c00,%fs
     445:	64 a0 7b 00          	mov    %fs:0x7b,%al
     449:	fb                   	sti    
     44a:	26 88 86 e8 02       	mov    %al,%es:0x2e8(%bp)
     44f:	26 0f b6 9e b1 02    	movzbw %es:0x2b1(%bp),%bx
     455:	26 80 be bc 02 8f    	cmpb   $0x8f,%es:0x2bc(%bp)
     45b:	75 15                	jne    0x472
     45d:	80 fb fe             	cmp    $0xfe,%bl
     460:	0f 84 86 01          	je     0x5ea
     464:	80 fb ff             	cmp    $0xff,%bl
     467:	0f 84 23 01          	je     0x58e
     46b:	80 fb fd             	cmp    $0xfd,%bl
     46e:	0f 84 34 01          	je     0x5a6
     472:	80 fb 4e             	cmp    $0x4e,%bl
     475:	73 06                	jae    0x47d
     477:	d1 e3                	shl    %bx
     479:	ff a7 1c 1c          	jmp    *0x1c1c(%bx)
     47d:	b4 01                	mov    $0x1,%ah
     47f:	80 fc 01             	cmp    $0x1,%ah
     482:	f5                   	cmc    
     483:	fb                   	sti    
     484:	26 88 a6 b1 02       	mov    %ah,%es:0x2b1(%bp)
     489:	9c                   	pushf  
     48a:	72 02                	jb     0x48e
     48c:	b4 00                	mov    $0x0,%ah
     48e:	fa                   	cli    
     48f:	8e 26 00 1c          	mov    0x1c00,%fs
     493:	64 88 26 74 00       	mov    %ah,%fs:0x74
     498:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
     49e:	75 0b                	jne    0x4ab
     4a0:	26 80 be e9 02 00    	cmpb   $0x0,%es:0x2e9(%bp)
     4a6:	75 03                	jne    0x4ab
     4a8:	e8 48 0d             	call   0x11f3
     4ab:	9d                   	popf   
     4ac:	66 26 8b 86 b0 02    	mov    %es:0x2b0(%bp),%eax
     4b2:	66 26 8b 9e b4 02    	mov    %es:0x2b4(%bp),%ebx
     4b8:	66 26 8b 8e b8 02    	mov    %es:0x2b8(%bp),%ecx
     4be:	66 26 8b 96 bc 02    	mov    %es:0x2bc(%bp),%edx
     4c4:	66 26 8b b6 c4 02    	mov    %es:0x2c4(%bp),%esi
     4ca:	66 26 8b be c0 02    	mov    %es:0x2c0(%bp),%edi
     4d0:	26 8e 9e c8 02       	mov    %es:0x2c8(%bp),%ds
     4d5:	26 8e ae cc 02       	mov    %es:0x2cc(%bp),%gs
     4da:	26 8e a6 ce 02       	mov    %es:0x2ce(%bp),%fs
     4df:	26 8e 86 ca 02       	mov    %es:0x2ca(%bp),%es
     4e4:	66 5d                	pop    %ebp
     4e6:	ca 02 00             	lret   $0x2
     4e9:	b4 07                	mov    $0x7,%ah
     4eb:	f9                   	stc    
     4ec:	eb 95                	jmp    0x483
     4ee:	b4 01                	mov    $0x1,%ah
     4f0:	eb 8d                	jmp    0x47f
     4f2:	33 c0                	xor    %ax,%ax
     4f4:	eb 8d                	jmp    0x483
     4f6:	e8 a3 0a             	call   0xf9c
     4f9:	72 f3                	jb     0x4ee
     4fb:	fa                   	cli    
     4fc:	e8 00 09             	call   0xdff
     4ff:	33 c0                	xor    %ax,%ax
     501:	eb 80                	jmp    0x483
     503:	fa                   	cli    
     504:	8e 26 00 1c          	mov    0x1c00,%fs
     508:	64 8a 26 74 00       	mov    %fs:0x74,%ah
     50d:	e9 6f ff             	jmp    0x47f
     510:	e8 89 0a             	call   0xf9c
     513:	72 d4                	jb     0x4e9
     515:	74 1f                	je     0x536
     517:	e8 20 08             	call   0xd3a
     51a:	75 cd                	jne    0x4e9
     51c:	66 26 8b 86 14 03    	mov    %es:0x314(%bp),%eax
     522:	26 89 86 bc 02       	mov    %ax,%es:0x2bc(%bp)
     527:	66 c1 e8 10          	shr    $0x10,%eax
     52b:	26 89 86 b8 02       	mov    %ax,%es:0x2b8(%bp)
     530:	b4 03                	mov    $0x3,%ah
     532:	f8                   	clc    
     533:	e9 4d ff             	jmp    0x483
     536:	66 a1 10 1c          	mov    0x1c10,%eax
     53a:	66 c1 e0 02          	shl    $0x2,%eax
     53e:	80 3e e7 1b 00       	cmpb   $0x0,0x1be7
     543:	75 dd                	jne    0x522
     545:	b4 01                	mov    $0x1,%ah
     547:	eb e9                	jmp    0x532
     549:	e8 50 0a             	call   0xf9c
     54c:	72 9b                	jb     0x4e9
     54e:	74 0e                	je     0x55e
     550:	e8 e7 07             	call   0xd3a
     553:	75 94                	jne    0x4e9
     555:	8b 1e f6 1b          	mov    0x1bf6,%bx
     559:	e8 8b 0a             	call   0xfe7
     55c:	eb 94                	jmp    0x4f2
     55e:	80 3e e7 1b 00       	cmpb   $0x0,0x1be7
     563:	74 0c                	je     0x571
     565:	a1 fa 1b             	mov    0x1bfa,%ax
     568:	8b 1e f8 1b          	mov    0x1bf8,%bx
     56c:	e8 9b 0a             	call   0x100a
     56f:	eb 81                	jmp    0x4f2
     571:	a0 e8 1b             	mov    0x1be8,%al
     574:	26 88 86 b4 02       	mov    %al,%es:0x2b4(%bp)
     579:	26 8c 9e ca 02       	mov    %ds,%es:0x2ca(%bp)
     57e:	26 c7 86 c0 02 ea 1b 	movw   $0x1bea,%es:0x2c0(%bp)
     585:	26 c6 86 bc 02 01    	movb   $0x1,%es:0x2bc(%bp)
     58b:	e9 64 ff             	jmp    0x4f2
     58e:	a0 54 01             	mov    0x154,%al
     591:	02 06 55 01          	add    0x155,%al
     595:	26 88 86 bd 02       	mov    %al,%es:0x2bd(%bp)
     59a:	26 c6 86 b0 02 0a    	movb   $0xa,%es:0x2b0(%bp)
     5a0:	b4 04                	mov    $0x4,%ah
     5a2:	f8                   	clc    
     5a3:	e9 dd fe             	jmp    0x483
     5a6:	fa                   	cli    
     5a7:	26 8e ae b4 02       	mov    %es:0x2b4(%bp),%gs
     5ac:	26 8b 9e b8 02       	mov    %es:0x2b8(%bp),%bx
     5b1:	65 0f b6 07          	movzbw %gs:(%bx),%ax
     5b5:	2a 06 54 01          	sub    0x154,%al
     5b9:	0f 82 31 ff          	jb     0x4ee
     5bd:	3a 06 55 01          	cmp    0x155,%al
     5c1:	0f 83 29 ff          	jae    0x4ee
     5c5:	65 0f b4 77 04       	lfs    %gs:0x4(%bx),%si
     5ca:	8b d8                	mov    %ax,%bx
     5cc:	64 c6 44 02 01       	movb   $0x1,%fs:0x2(%si)
     5d1:	8a 87 d1 00          	mov    0xd1(%bx),%al
     5d5:	64 88 44 03          	mov    %al,%fs:0x3(%si)
     5d9:	d1 e3                	shl    %bx
     5db:	8b 87 a0 00          	mov    0xa0(%bx),%ax
     5df:	64 89 04             	mov    %ax,%fs:(%si)
     5e2:	64 c6 44 04 00       	movb   $0x0,%fs:0x4(%si)
     5e7:	e9 08 ff             	jmp    0x4f2
     5ea:	26 8e ae b4 02       	mov    %es:0x2b4(%bp),%gs
     5ef:	26 8b 9e b8 02       	mov    %es:0x2b8(%bp),%bx
     5f4:	65 0f b6 07          	movzbw %gs:(%bx),%ax
     5f8:	2a 06 54 01          	sub    0x154,%al
     5fc:	0f 82 ee fe          	jb     0x4ee
     600:	3a 06 55 01          	cmp    0x155,%al
     604:	0f 83 e6 fe          	jae    0x4ee
     608:	26 88 86 e2 02       	mov    %al,%es:0x2e2(%bp)
     60d:	66 65 8b 47 0b       	mov    %gs:0xb(%bx),%eax
     612:	66 26 89 86 d0 02    	mov    %eax,%es:0x2d0(%bp)
     618:	66 65 8b 47 0f       	mov    %gs:0xf(%bx),%eax
     61d:	66 26 89 86 d4 02    	mov    %eax,%es:0x2d4(%bp)
     623:	66 65 8b 47 13       	mov    %gs:0x13(%bx),%eax
     628:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     62e:	66 65 8b 47 17       	mov    %gs:0x17(%bx),%eax
     633:	66 26 89 86 dc 02    	mov    %eax,%es:0x2dc(%bp)
     639:	26 c6 86 00 03 00    	movb   $0x0,%es:0x300(%bp)
     63f:	26 c6 86 01 03 00    	movb   $0x0,%es:0x301(%bp)
     645:	66 b8 12 00 00 00    	mov    $0x12,%eax
     64b:	65 f6 67 0a          	mulb   %gs:0xa(%bx)
     64f:	66 26 89 86 10 03    	mov    %eax,%es:0x310(%bp)
     655:	65 f6 47 01 0c       	testb  $0xc,%gs:0x1(%bx)
     65a:	0f 84 ab 00          	je     0x709
     65e:	65 8b 57 06          	mov    %gs:0x6(%bx),%dx
     662:	65 8b 47 04          	mov    %gs:0x4(%bx),%ax
     666:	e8 12 0a             	call   0x107b
     669:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     66f:	26 f6 86 e8 02 20    	testb  $0x20,%es:0x2e8(%bp)
     675:	0f 84 90 00          	je     0x709
     679:	66 65 0f b7 47 08    	movzwl %gs:0x8(%bx),%eax
     67f:	0b c0                	or     %ax,%ax
     681:	75 06                	jne    0x689
     683:	66 b8 00 00 01 00    	mov    $0x10000,%eax
     689:	66 26 89 46 30       	mov    %eax,%es:0x30(%bp)
     68e:	66 26 89 86 50 01    	mov    %eax,%es:0x150(%bp)
     694:	66 65 0f b7 47 04    	movzwl %gs:0x4(%bx),%eax
     69a:	66 26 89 46 34       	mov    %eax,%es:0x34(%bp)
     69f:	66 26 89 86 54 01    	mov    %eax,%es:0x154(%bp)
     6a5:	66 65 0f b7 47 06    	movzwl %gs:0x6(%bx),%eax
     6ab:	66 26 89 46 38       	mov    %eax,%es:0x38(%bp)
     6b0:	26 89 86 58 01       	mov    %ax,%es:0x158(%bp)
     6b5:	65 f6 47 01 08       	testb  $0x8,%gs:0x1(%bx)
     6ba:	74 22                	je     0x6de
     6bc:	65 c6 47 19 01       	movb   $0x1,%gs:0x19(%bx)
     6c1:	26 c7 46 3c 22 00    	movw   $0x22,%es:0x3c(%bp)
     6c7:	e8 79 10             	call   0x1743
     6ca:	8c c2                	mov    %es,%dx
     6cc:	8d 46 40             	lea    0x40(%bp),%ax
     6cf:	e8 a9 09             	call   0x107b
     6d2:	66 83 e8 08          	sub    $0x8,%eax
     6d6:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     6dc:	eb 2b                	jmp    0x709
     6de:	65 c6 47 18 01       	movb   $0x1,%gs:0x18(%bx)
     6e3:	ba 08 00             	mov    $0x8,%dx
     6e6:	65 f6 47 01 02       	testb  $0x2,%gs:0x1(%bx)
     6eb:	74 03                	je     0x6f0
     6ed:	ba 0a 00             	mov    $0xa,%dx
     6f0:	b8 03 81             	mov    $0x8103,%ax
     6f3:	8d be 50 01          	lea    0x150(%bp),%di
     6f7:	cd 4b                	int    $0x4b
     6f9:	0f 82 62 10          	jb     0x175f
     6fd:	66 26 8b 86 5c 01    	mov    %es:0x15c(%bp),%eax
     703:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     709:	e8 85 06             	call   0xd91
     70c:	26 8b 9e b8 02       	mov    %es:0x2b8(%bp),%bx
     711:	65 89 47 02          	mov    %ax,%gs:0x2(%bx)
     715:	65 80 7f 19 00       	cmpb   $0x0,%gs:0x19(%bx)
     71a:	74 03                	je     0x71f
     71c:	e8 38 10             	call   0x1757
     71f:	65 80 7f 18 00       	cmpb   $0x0,%gs:0x18(%bx)
     724:	0f 84 ca fd          	je     0x4f2
     728:	ba 00 00             	mov    $0x0,%dx
     72b:	65 f6 47 01 01       	testb  $0x1,%gs:0x1(%bx)
     730:	74 03                	je     0x735
     732:	ba 02 00             	mov    $0x2,%dx
     735:	b8 04 81             	mov    $0x8104,%ax
     738:	8d be 50 01          	lea    0x150(%bp),%di
     73c:	cd 4b                	int    $0x4b
     73e:	0f 82 1d 10          	jb     0x175f
     742:	e9 ad fd             	jmp    0x4f2
     745:	26 c6 86 d0 02 37    	movb   $0x37,%es:0x2d0(%bp)
     74b:	eb 06                	jmp    0x753
     74d:	26 c6 86 d0 02 36    	movb   $0x36,%es:0x2d0(%bp)
     753:	26 8b 86 ca 02       	mov    %es:0x2ca(%bp),%ax
     758:	66 c1 e0 10          	shl    $0x10,%eax
     75c:	26 8b 86 b4 02       	mov    %es:0x2b4(%bp),%ax
     761:	66 26 89 86 f8 02    	mov    %eax,%es:0x2f8(%bp)
     767:	66 26 0f b6 86 b0 02 	movzbl %es:0x2b0(%bp),%eax
     76e:	66 26 89 86 f4 02    	mov    %eax,%es:0x2f4(%bp)
     774:	66 c1 e0 09          	shl    $0x9,%eax
     778:	66 26 89 86 fc 02    	mov    %eax,%es:0x2fc(%bp)
     77e:	e8 1b 08             	call   0xf9c
     781:	72 6e                	jb     0x7f1
     783:	74 71                	je     0x7f6
     785:	8b 1e f6 1b          	mov    0x1bf6,%bx
     789:	e8 9b 08             	call   0x1027
     78c:	66 26 89 86 f0 02    	mov    %eax,%es:0x2f0(%bp)
     792:	66 26 8b 86 f0 02    	mov    %es:0x2f0(%bp),%eax
     798:	66 26 89 86 d4 02    	mov    %eax,%es:0x2d4(%bp)
     79e:	26 8a 86 f4 02       	mov    %es:0x2f4(%bp),%al
     7a3:	26 88 86 d2 02       	mov    %al,%es:0x2d2(%bp)
     7a8:	26 8a 86 e3 02       	mov    %es:0x2e3(%bp),%al
     7ad:	c0 e0 03             	shl    $0x3,%al
     7b0:	26 88 86 d3 02       	mov    %al,%es:0x2d3(%bp)
     7b5:	26 c6 86 dc 02 00    	movb   $0x0,%es:0x2dc(%bp)
     7bb:	26 8b 96 fa 02       	mov    %es:0x2fa(%bp),%dx
     7c0:	26 8b 86 f8 02       	mov    %es:0x2f8(%bp),%ax
     7c5:	26 f6 86 e8 02 20    	testb  $0x20,%es:0x2e8(%bp)
     7cb:	74 1d                	je     0x7ea
     7cd:	26 80 8e d0 02 80    	orb    $0x80,%es:0x2d0(%bp)
     7d3:	26 c7 46 3c 22 00    	movw   $0x22,%es:0x3c(%bp)
     7d9:	e8 3f 0f             	call   0x171b
     7dc:	26 8b 46 3e          	mov    %es:0x3e(%bp),%ax
     7e0:	26 88 86 dc 02       	mov    %al,%es:0x2dc(%bp)
     7e5:	8d 46 40             	lea    0x40(%bp),%ax
     7e8:	8c c2                	mov    %es,%dx
     7ea:	e8 ff 03             	call   0xbec
     7ed:	0f 84 8e fc          	je     0x47f
     7f1:	b4 bb                	mov    $0xbb,%ah
     7f3:	e9 89 fc             	jmp    0x47f
     7f6:	26 80 be d0 02 37    	cmpb   $0x37,%es:0x2d0(%bp)
     7fc:	b4 03                	mov    $0x3,%ah
     7fe:	0f 84 7d fc          	je     0x47f
     802:	66 26 c7 86 2a 03 00 	movl   $0x0,%es:0x32a(%bp)
     809:	00 00 00 
     80c:	66 26 c7 86 2e 03 00 	movl   $0x0,%es:0x32e(%bp)
     813:	00 00 00 
     816:	66 26 c7 86 32 03 00 	movl   $0x0,%es:0x332(%bp)
     81d:	00 00 00 
     820:	66 26 c7 86 d0 02 00 	movl   $0x0,%es:0x2d0(%bp)
     827:	00 00 00 
     82a:	66 26 c7 86 d4 02 00 	movl   $0x0,%es:0x2d4(%bp)
     831:	00 00 00 
     834:	66 26 c7 86 d8 02 00 	movl   $0x0,%es:0x2d8(%bp)
     83b:	00 00 00 
     83e:	66 26 c7 86 dc 02 00 	movl   $0x0,%es:0x2dc(%bp)
     845:	00 00 00 
     848:	8b 1e f8 1b          	mov    0x1bf8,%bx
     84c:	e8 d8 07             	call   0x1027
     84f:	8c c2                	mov    %es,%dx
     851:	8d 86 80 03          	lea    0x380(%bp),%ax
     855:	e8 23 08             	call   0x107b
     858:	b9 22 00             	mov    $0x22,%cx
     85b:	33 ff                	xor    %di,%di
     85d:	66 26 89 83 60 01    	mov    %eax,%es:0x160(%bp,%di)
     863:	66 26 c7 83 64 01 00 	movl   $0x200,%es:0x164(%bp,%di)
     86a:	02 00 00 
     86d:	83 c7 08             	add    $0x8,%di
     870:	e2 eb                	loop   0x85d
     872:	26 8b 96 fa 02       	mov    %es:0x2fa(%bp),%dx
     877:	26 8b 86 f8 02       	mov    %es:0x2f8(%bp),%ax
     87c:	e8 fc 07             	call   0x107b
     87f:	66 26 89 46 40       	mov    %eax,%es:0x40(%bp)
     884:	66 26 0f b6 86 f4 02 	movzbl %es:0x2f4(%bp),%eax
     88b:	66 c1 e0 09          	shl    $0x9,%eax
     88f:	66 26 89 46 44       	mov    %eax,%es:0x44(%bp)
     894:	26 c7 46 3e 01 00    	movw   $0x1,%es:0x3e(%bp)
     89a:	26 f6 86 e8 02 20    	testb  $0x20,%es:0x2e8(%bp)
     8a0:	74 09                	je     0x8ab
     8a2:	26 c7 46 3c 1f 00    	movw   $0x1f,%es:0x3c(%bp)
     8a8:	e8 70 0e             	call   0x171b
     8ab:	26 c6 86 2a 03 28    	movb   $0x28,%es:0x32a(%bp)
     8b1:	26 c6 86 21 03 a1    	movb   $0xa1,%es:0x321(%bp)
     8b7:	26 8a 86 14 03       	mov    %es:0x314(%bp),%al
     8bc:	83 e0 03             	and    $0x3,%ax
     8bf:	26 88 86 d2 02       	mov    %al,%es:0x2d2(%bp)
     8c4:	c1 e0 03             	shl    $0x3,%ax
     8c7:	8d be 60 01          	lea    0x160(%bp),%di
     8cb:	03 f8                	add    %ax,%di
     8cd:	8d 76 40             	lea    0x40(%bp),%si
     8d0:	26 8b 4e 3e          	mov    %es:0x3e(%bp),%cx
     8d4:	26 00 8e d2 02       	add    %cl,%es:0x2d2(%bp)
     8d9:	c1 e1 02             	shl    $0x2,%cx
     8dc:	fc                   	cld    
     8dd:	f3 26 a5             	rep movsw %es:(%si),%es:(%di)
     8e0:	26 8a 86 14 03       	mov    %es:0x314(%bp),%al
     8e5:	26 02 86 f4 02       	add    %es:0x2f4(%bp),%al
     8ea:	24 03                	and    $0x3,%al
     8ec:	b1 04                	mov    $0x4,%cl
     8ee:	2a c8                	sub    %al,%cl
     8f0:	83 e1 03             	and    $0x3,%cx
     8f3:	26 02 8e d2 02       	add    %es:0x2d2(%bp),%cl
     8f8:	26 88 8e d2 02       	mov    %cl,%es:0x2d2(%bp)
     8fd:	66 33 c0             	xor    %eax,%eax
     900:	8d be 64 01          	lea    0x164(%bp),%di
     904:	66 26 03 05          	add    %es:(%di),%eax
     908:	83 c7 08             	add    $0x8,%di
     90b:	e2 f7                	loop   0x904
     90d:	26 89 86 22 03       	mov    %ax,%es:0x322(%bp)
     912:	66 26 89 86 fc 02    	mov    %eax,%es:0x2fc(%bp)
     918:	66 8b d0             	mov    %eax,%edx
     91b:	66 c1 ea 0c          	shr    $0xc,%edx
     91f:	80 e2 f0             	and    $0xf0,%dl
     922:	80 ca 0a             	or     $0xa,%dl
     925:	26 88 96 28 03       	mov    %dl,%es:0x328(%bp)
     92a:	66 33 d2             	xor    %edx,%edx
     92d:	66 b9 00 08 00 00    	mov    $0x800,%ecx
     933:	66 f7 f1             	div    %ecx
     936:	26 88 a6 31 03       	mov    %ah,%es:0x331(%bp)
     93b:	26 88 86 32 03       	mov    %al,%es:0x332(%bp)
     940:	8c c2                	mov    %es,%dx
     942:	8d 86 60 01          	lea    0x160(%bp),%ax
     946:	e8 32 07             	call   0x107b
     949:	66 83 e8 08          	sub    $0x8,%eax
     94d:	66 26 89 86 24 03    	mov    %eax,%es:0x324(%bp)
     953:	66 26 8b 86 14 03    	mov    %es:0x314(%bp),%eax
     959:	66 c1 e8 02          	shr    $0x2,%eax
     95d:	66 03 06 0c 1c       	add    0x1c0c,%eax
     962:	66 26 89 86 f0 02    	mov    %eax,%es:0x2f0(%bp)
     968:	e8 fa 06             	call   0x1065
     96b:	66 26 89 86 2c 03    	mov    %eax,%es:0x32c(%bp)
     971:	2e a0 e5 1b          	mov    %cs:0x1be5,%al
     975:	26 88 86 20 03       	mov    %al,%es:0x320(%bp)
     97a:	26 c6 86 d0 02 84    	movb   $0x84,%es:0x2d0(%bp)
     980:	8d 86 20 03          	lea    0x320(%bp),%ax
     984:	8c c2                	mov    %es,%dx
     986:	e9 61 fe             	jmp    0x7ea
     989:	26 8e ae c8 02       	mov    %es:0x2c8(%bp),%gs
     98e:	26 8b 9e c4 02       	mov    %es:0x2c4(%bp),%bx
     993:	66 65 8b 47 08       	mov    %gs:0x8(%bx),%eax
     998:	66 26 89 86 f0 02    	mov    %eax,%es:0x2f0(%bp)
     99e:	66 65 8b 47 04       	mov    %gs:0x4(%bx),%eax
     9a3:	66 26 89 86 f8 02    	mov    %eax,%es:0x2f8(%bp)
     9a9:	66 65 0f b7 47 02    	movzwl %gs:0x2(%bx),%eax
     9af:	66 26 89 86 f4 02    	mov    %eax,%es:0x2f4(%bp)
     9b5:	66 c1 e0 09          	shl    $0x9,%eax
     9b9:	66 26 89 86 fc 02    	mov    %eax,%es:0x2fc(%bp)
     9bf:	c3                   	ret    
     9c0:	e8 3f 02             	call   0xc02
     9c3:	0f 82 27 fb          	jb     0x4ee
     9c7:	e9 28 fb             	jmp    0x4f2
     9ca:	e8 35 02             	call   0xc02
     9cd:	0f 82 ae fa          	jb     0x47f
     9d1:	26 80 be b0 02 01    	cmpb   $0x1,%es:0x2b0(%bp)
     9d7:	0f 85 13 fb          	jne    0x4ee
     9db:	65 c6 07 13          	movb   $0x13,%gs:(%bx)
     9df:	a0 e7 1b             	mov    0x1be7,%al
     9e2:	65 88 47 02          	mov    %al,%gs:0x2(%bx)
     9e6:	65 c6 47 01 00       	movb   $0x0,%gs:0x1(%bx)
     9eb:	66 65 c7 47 03 00 00 	movl   $0x0,%gs:0x3(%bx)
     9f2:	00 00 
     9f4:	66 65 c7 47 07 00 00 	movl   $0x0,%gs:0x7(%bx)
     9fb:	00 00 
     9fd:	66 65 c7 47 0b 00 00 	movl   $0x0,%gs:0xb(%bx)
     a04:	00 00 
     a06:	66 65 c7 47 0f 00 00 	movl   $0x0,%gs:0xf(%bx)
     a0d:	00 00 
     a0f:	e9 e0 fa             	jmp    0x4f2
     a12:	e8 ed 01             	call   0xc02
     a15:	72 26                	jb     0xa3d
     a17:	65 c7 07 1a 00       	movw   $0x1a,%gs:(%bx)
     a1c:	65 c7 47 02 45 00    	movw   $0x45,%gs:0x2(%bx)
     a22:	66 a1 10 1c          	mov    0x1c10,%eax
     a26:	66 65 89 47 10       	mov    %eax,%gs:0x10(%bx)
     a2b:	66 65 c7 47 14 00 00 	movl   $0x0,%gs:0x14(%bx)
     a32:	00 00 
     a34:	65 c7 47 18 00 08    	movw   $0x800,%gs:0x18(%bx)
     a3a:	e9 b5 fa             	jmp    0x4f2
     a3d:	e8 5c 05             	call   0xf9c
     a40:	0f 82 3b fa          	jb     0x47f
     a44:	0f 84 37 fa          	je     0x47f
     a48:	e8 ef 02             	call   0xd3a
     a4b:	0f 85 9a fa          	jne    0x4e9
     a4f:	26 8e ae c8 02       	mov    %es:0x2c8(%bp),%gs
     a54:	26 8b 9e c4 02       	mov    %es:0x2c4(%bp),%bx
     a59:	65 c7 07 1a 00       	movw   $0x1a,%gs:(%bx)
     a5e:	65 c7 47 02 09 00    	movw   $0x9,%gs:0x2(%bx)
     a64:	66 26 8b 86 14 03    	mov    %es:0x314(%bp),%eax
     a6a:	66 65 89 47 10       	mov    %eax,%gs:0x10(%bx)
     a6f:	66 65 c7 47 14 00 00 	movl   $0x0,%gs:0x14(%bx)
     a76:	00 00 
     a78:	65 c7 47 18 00 02    	movw   $0x200,%gs:0x18(%bx)
     a7e:	e9 71 fa             	jmp    0x4f2
     a81:	e8 18 05             	call   0xf9c
     a84:	73 07                	jae    0xa8d
     a86:	e8 79 01             	call   0xc02
     a89:	0f 82 f2 f9          	jb     0x47f
     a8d:	26 c7 86 b4 02 55 aa 	movw   $0xaa55,%es:0x2b4(%bp)
     a94:	26 c7 86 b8 02 01 00 	movw   $0x1,%es:0x2b8(%bp)
     a9b:	26 c6 86 b0 02 00    	movb   $0x0,%es:0x2b0(%bp)
     aa1:	b4 01                	mov    $0x1,%ah
     aa3:	e9 dd f9             	jmp    0x483
     aa6:	26 c6 86 d0 02 37    	movb   $0x37,%es:0x2d0(%bp)
     aac:	e8 da fe             	call   0x989
     aaf:	e8 50 01             	call   0xc02
     ab2:	b4 03                	mov    $0x3,%ah
     ab4:	0f 83 c7 f9          	jae    0x47f
     ab8:	e8 e1 04             	call   0xf9c
     abb:	0f 82 32 fd          	jb     0x7f1
     abf:	0f 84 2e fd          	je     0x7f1
     ac3:	e9 cc fc             	jmp    0x792
     ac6:	26 c6 86 d0 02 36    	movb   $0x36,%es:0x2d0(%bp)
     acc:	e8 ba fe             	call   0x989
     acf:	e8 30 01             	call   0xc02
     ad2:	72 e4                	jb     0xab8
     ad4:	a0 e6 1b             	mov    0x1be6,%al
     ad7:	26 88 86 e2 02       	mov    %al,%es:0x2e2(%bp)
     adc:	e8 09 00             	call   0xae8
     adf:	0f 84 9c f9          	je     0x47f
     ae3:	b4 bb                	mov    $0xbb,%ah
     ae5:	e9 97 f9             	jmp    0x47f
     ae8:	66 26 c7 86 2a 03 00 	movl   $0x0,%es:0x32a(%bp)
     aef:	00 00 00 
     af2:	66 26 c7 86 2e 03 00 	movl   $0x0,%es:0x32e(%bp)
     af9:	00 00 00 
     afc:	66 26 c7 86 32 03 00 	movl   $0x0,%es:0x332(%bp)
     b03:	00 00 00 
     b06:	66 26 c7 86 d0 02 00 	movl   $0x0,%es:0x2d0(%bp)
     b0d:	00 00 00 
     b10:	66 26 c7 86 d4 02 00 	movl   $0x0,%es:0x2d4(%bp)
     b17:	00 00 00 
     b1a:	66 26 c7 86 d8 02 00 	movl   $0x0,%es:0x2d8(%bp)
     b21:	00 00 00 
     b24:	66 26 c7 86 dc 02 00 	movl   $0x0,%es:0x2dc(%bp)
     b2b:	00 00 00 
     b2e:	26 8b 96 fa 02       	mov    %es:0x2fa(%bp),%dx
     b33:	26 8b 86 f8 02       	mov    %es:0x2f8(%bp),%ax
     b38:	e8 40 05             	call   0x107b
     b3b:	66 26 89 46 40       	mov    %eax,%es:0x40(%bp)
     b40:	66 26 8b 86 f4 02    	mov    %es:0x2f4(%bp),%eax
     b46:	26 88 a6 31 03       	mov    %ah,%es:0x331(%bp)
     b4b:	26 88 86 32 03       	mov    %al,%es:0x332(%bp)
     b50:	66 c1 e0 0b          	shl    $0xb,%eax
     b54:	66 26 89 46 44       	mov    %eax,%es:0x44(%bp)
     b59:	66 26 89 46 30       	mov    %eax,%es:0x30(%bp)
     b5e:	66 26 89 86 fc 02    	mov    %eax,%es:0x2fc(%bp)
     b64:	26 c7 46 3e 01 00    	movw   $0x1,%es:0x3e(%bp)
     b6a:	26 89 86 22 03       	mov    %ax,%es:0x322(%bp)
     b6f:	66 8b d0             	mov    %eax,%edx
     b72:	66 c1 ea 0c          	shr    $0xc,%edx
     b76:	80 e2 f0             	and    $0xf0,%dl
     b79:	80 ca 0a             	or     $0xa,%dl
     b7c:	26 88 96 28 03       	mov    %dl,%es:0x328(%bp)
     b81:	26 f6 86 e8 02 20    	testb  $0x20,%es:0x2e8(%bp)
     b87:	74 09                	je     0xb92
     b89:	26 c7 46 3c 22 00    	movw   $0x22,%es:0x3c(%bp)
     b8f:	e8 99 0b             	call   0x172b
     b92:	26 c6 86 2a 03 28    	movb   $0x28,%es:0x32a(%bp)
     b98:	26 c6 86 21 03 a1    	movb   $0xa1,%es:0x321(%bp)
     b9e:	8d be 60 01          	lea    0x160(%bp),%di
     ba2:	8d 76 40             	lea    0x40(%bp),%si
     ba5:	26 8b 4e 3e          	mov    %es:0x3e(%bp),%cx
     ba9:	26 88 8e d2 02       	mov    %cl,%es:0x2d2(%bp)
     bae:	c1 e1 02             	shl    $0x2,%cx
     bb1:	fc                   	cld    
     bb2:	f3 26 a5             	rep movsw %es:(%si),%es:(%di)
     bb5:	8c c2                	mov    %es,%dx
     bb7:	8d 86 60 01          	lea    0x160(%bp),%ax
     bbb:	e8 bd 04             	call   0x107b
     bbe:	66 83 e8 08          	sub    $0x8,%eax
     bc2:	66 26 89 86 24 03    	mov    %eax,%es:0x324(%bp)
     bc8:	66 26 8b 86 f0 02    	mov    %es:0x2f0(%bp),%eax
     bce:	e8 94 04             	call   0x1065
     bd1:	66 26 89 86 2c 03    	mov    %eax,%es:0x32c(%bp)
     bd7:	2e a0 e5 1b          	mov    %cs:0x1be5,%al
     bdb:	26 88 86 20 03       	mov    %al,%es:0x320(%bp)
     be0:	26 c6 86 d0 02 84    	movb   $0x84,%es:0x2d0(%bp)
     be6:	8d 86 20 03          	lea    0x320(%bp),%ax
     bea:	8c c2                	mov    %es,%dx
     bec:	e8 34 00             	call   0xc23
     bef:	26 f6 86 e8 02 20    	testb  $0x20,%es:0x2e8(%bp)
     bf5:	74 03                	je     0xbfa
     bf7:	e8 5d 0b             	call   0x1757
     bfa:	26 8b 86 e0 02       	mov    %es:0x2e0(%bp),%ax
     bff:	0b c0                	or     %ax,%ax
     c01:	c3                   	ret    
     c02:	80 3e e3 1b 00       	cmpb   $0x0,0x1be3
     c07:	74 16                	je     0xc1f
     c09:	26 8a 86 bc 02       	mov    %es:0x2bc(%bp),%al
     c0e:	38 06 e7 1b          	cmp    %al,0x1be7
     c12:	75 0b                	jne    0xc1f
     c14:	26 8e ae c8 02       	mov    %es:0x2c8(%bp),%gs
     c19:	26 8b 9e c4 02       	mov    %es:0x2c4(%bp),%bx
     c1e:	c3                   	ret    
     c1f:	b4 01                	mov    $0x1,%ah
     c21:	f9                   	stc    
     c22:	c3                   	ret    
     c23:	e8 55 04             	call   0x107b
     c26:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     c2c:	26 80 be d0 02 84    	cmpb   $0x84,%es:0x2d0(%bp)
     c32:	0f 85 4b 01          	jne    0xd81
     c36:	66 26 81 be fc 02 fe 	cmpl   $0xfffe,%es:0x2fc(%bp)
     c3d:	ff 00 00 
     c40:	0f 86 3d 01          	jbe    0xd81
     c44:	b8 10 00             	mov    $0x10,%ax
     c47:	83 f8 02             	cmp    $0x2,%ax
     c4a:	0f 85 33 01          	jne    0xd81
     c4e:	26 c6 86 d2 02 00    	movb   $0x0,%es:0x2d2(%bp)
     c54:	8d b6 58 01          	lea    0x158(%bp),%si
     c58:	66 b9 00 f0 00 00    	mov    $0xf000,%ecx
     c5e:	83 c6 08             	add    $0x8,%si
     c61:	26 80 86 d2 02 01    	addb   $0x1,%es:0x2d2(%bp)
     c67:	66 26 2b 4c 04       	sub    %es:0x4(%si),%ecx
     c6c:	73 f0                	jae    0xc5e
     c6e:	66 26 03 4c 04       	add    %es:0x4(%si),%ecx
     c73:	66 26 87 4c 04       	xchg   %ecx,%es:0x4(%si)
     c78:	66 26 2b 4c 04       	sub    %es:0x4(%si),%ecx
     c7d:	b8 1e 00             	mov    $0x1e,%ax
     c80:	26 88 a6 31 03       	mov    %ah,%es:0x331(%bp)
     c85:	26 88 86 32 03       	mov    %al,%es:0x332(%bp)
     c8a:	26 c7 86 22 03 00 f0 	movw   $0xf000,%es:0x322(%bp)
     c91:	26 80 a6 28 03 0f    	andb   $0xf,%es:0x328(%bp)
     c97:	56                   	push   %si
     c98:	66 51                	push   %ecx
     c9a:	e8 e4 00             	call   0xd81
     c9d:	66 59                	pop    %ecx
     c9f:	5e                   	pop    %si
     ca0:	75 76                	jne    0xd18
     ca2:	66 26 8b 44 04       	mov    %es:0x4(%si),%eax
     ca7:	66 26 01 04          	add    %eax,%es:(%si)
     cab:	66 26 89 4c 04       	mov    %ecx,%es:0x4(%si)
     cb0:	8c c2                	mov    %es,%dx
     cb2:	8b c6                	mov    %si,%ax
     cb4:	e8 c4 03             	call   0x107b
     cb7:	66 83 e8 08          	sub    $0x8,%eax
     cbb:	66 26 89 86 24 03    	mov    %eax,%es:0x324(%bp)
     cc1:	66 26 8b 86 f0 02    	mov    %es:0x2f0(%bp),%eax
     cc7:	66 83 c0 1e          	add    $0x1e,%eax
     ccb:	e8 97 03             	call   0x1065
     cce:	66 26 89 86 2c 03    	mov    %eax,%es:0x32c(%bp)
     cd4:	66 26 8b 86 fc 02    	mov    %es:0x2fc(%bp),%eax
     cda:	66 2d 00 f0 00 00    	sub    $0xf000,%eax
     ce0:	26 89 86 22 03       	mov    %ax,%es:0x322(%bp)
     ce5:	66 50                	push   %eax
     ce7:	66 33 d2             	xor    %edx,%edx
     cea:	66 b9 00 08 00 00    	mov    $0x800,%ecx
     cf0:	66 f7 f1             	div    %ecx
     cf3:	26 88 a6 31 03       	mov    %ah,%es:0x331(%bp)
     cf8:	26 88 86 32 03       	mov    %al,%es:0x332(%bp)
     cfd:	26 c6 86 d2 02 00    	movb   $0x0,%es:0x2d2(%bp)
     d03:	66 59                	pop    %ecx
     d05:	26 80 86 d2 02 01    	addb   $0x1,%es:0x2d2(%bp)
     d0b:	66 26 2b 4c 04       	sub    %es:0x4(%si),%ecx
     d10:	8d 74 08             	lea    0x8(%si),%si
     d13:	75 f0                	jne    0xd05
     d15:	e8 69 00             	call   0xd81
     d18:	c3                   	ret    
     d19:	53                   	push   %bx
     d1a:	1e                   	push   %ds
     d1b:	2e 8e 1e 00 1c       	mov    %cs:0x1c00,%ds
     d20:	8a 1e 75 00          	mov    0x75,%bl
     d24:	2e 8a 3e d0 00       	mov    %cs:0xd0,%bh
     d29:	88 3e 75 00          	mov    %bh,0x75
     d2d:	9c                   	pushf  
     d2e:	2e ff 1e 50 01       	lcall  *%cs:0x150
     d33:	88 1e 75 00          	mov    %bl,0x75
     d37:	1f                   	pop    %ds
     d38:	5b                   	pop    %bx
     d39:	c3                   	ret    
     d3a:	66 26 c7 86 d0 02 00 	movl   $0x0,%es:0x2d0(%bp)
     d41:	00 00 00 
     d44:	66 26 c7 86 d4 02 00 	movl   $0x0,%es:0x2d4(%bp)
     d4b:	00 00 00 
     d4e:	66 26 c7 86 d8 02 00 	movl   $0x0,%es:0x2d8(%bp)
     d55:	00 00 00 
     d58:	66 26 c7 86 dc 02 00 	movl   $0x0,%es:0x2dc(%bp)
     d5f:	00 00 00 
     d62:	26 c6 86 d0 02 08    	movb   $0x8,%es:0x2d0(%bp)
     d68:	26 8a 86 e3 02       	mov    %es:0x2e3(%bp),%al
     d6d:	26 88 86 d7 02       	mov    %al,%es:0x2d7(%bp)
     d72:	8d 86 14 03          	lea    0x314(%bp),%ax
     d76:	8c c2                	mov    %es,%dx
     d78:	e8 00 03             	call   0x107b
     d7b:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     d81:	66 26 c7 86 10 03 50 	movl   $0x1950,%es:0x310(%bp)
     d88:	19 00 00 
     d8b:	26 c6 86 d1 02 ff    	movb   $0xff,%es:0x2d1(%bp)
     d91:	fa                   	cli    
     d92:	26 0f b6 9e e2 02    	movzbw %es:0x2e2(%bp),%bx
     d98:	c1 e3 02             	shl    $0x2,%bx
     d9b:	66 8b 87 10 01       	mov    0x110(%bx),%eax
     da0:	66 26 89 86 e4 02    	mov    %eax,%es:0x2e4(%bp)
     da6:	26 c6 86 29 03 40    	movb   $0x40,%es:0x329(%bp)
     dac:	e8 c2 07             	call   0x1571
     daf:	e8 d0 07             	call   0x1582
     db2:	e8 07 08             	call   0x15bc
     db5:	8e 26 00 1c          	mov    0x1c00,%fs
     db9:	66 64 8b 1e 6c 00    	mov    %fs:0x6c,%ebx
     dbf:	66 26 03 9e 10 03    	add    %es:0x310(%bp),%ebx
     dc5:	fb                   	sti    
     dc6:	fa                   	cli    
     dc7:	e8 7a 07             	call   0x1544
     dca:	e8 59 07             	call   0x1526
     dcd:	24 01                	and    $0x1,%al
     dcf:	75 18                	jne    0xde9
     dd1:	fb                   	sti    
     dd2:	b8 00 90             	mov    $0x9000,%ax
     dd5:	cd 15                	int    $0x15
     dd7:	fa                   	cli    
     dd8:	8e 26 00 1c          	mov    0x1c00,%fs
     ddc:	66 64 3b 1e 6c 00    	cmp    %fs:0x6c,%ebx
     de2:	77 e1                	ja     0xdc5
     de4:	b8 80 00             	mov    $0x80,%ax
     de7:	eb 03                	jmp    0xdec
     de9:	e8 b0 07             	call   0x159c
     dec:	26 89 86 e0 02       	mov    %ax,%es:0x2e0(%bp)
     df1:	b0 fb                	mov    $0xfb,%al
     df3:	e8 7d 07             	call   0x1573
     df6:	fb                   	sti    
     df7:	26 8b 86 e0 02       	mov    %es:0x2e0(%bp),%ax
     dfc:	0b c0                	or     %ax,%ax
     dfe:	c3                   	ret    
     dff:	26 0f b6 9e e2 02    	movzbw %es:0x2e2(%bp),%bx
     e05:	c1 e3 02             	shl    $0x2,%bx
     e08:	66 8b 87 10 01       	mov    0x110(%bx),%eax
     e0d:	66 26 89 86 e4 02    	mov    %eax,%es:0x2e4(%bp)
     e13:	e8 10 07             	call   0x1526
     e16:	24 01                	and    $0x1,%al
     e18:	75 01                	jne    0xe1b
     e1a:	c3                   	ret    
     e1b:	e8 7e 07             	call   0x159c
     e1e:	8e 26 00 1c          	mov    0x1c00,%fs
     e22:	66 64 8b 1e 6c 00    	mov    %fs:0x6c,%ebx
     e28:	66 83 c3 7e          	add    $0x7e,%ebx
     e2c:	fa                   	cli    
     e2d:	e8 f6 06             	call   0x1526
     e30:	24 01                	and    $0x1,%al
     e32:	75 e7                	jne    0xe1b
     e34:	fb                   	sti    
     e35:	b8 00 90             	mov    $0x9000,%ax
     e38:	cd 15                	int    $0x15
     e3a:	fa                   	cli    
     e3b:	8e 26 00 1c          	mov    0x1c00,%fs
     e3f:	66 64 3b 1e 6c 00    	cmp    %fs:0x6c,%ebx
     e45:	77 e5                	ja     0xe2c
     e47:	c3                   	ret    
     e48:	80 3e e1 1b 00       	cmpb   $0x0,0x1be1
     e4d:	74 03                	je     0xe52
     e4f:	33 c0                	xor    %ax,%ax
     e51:	c3                   	ret    
     e52:	26 c6 86 d0 02 2b    	movb   $0x2b,%es:0x2d0(%bp)
     e58:	26 c6 86 d2 02 02    	movb   $0x2,%es:0x2d2(%bp)
     e5e:	e8 20 ff             	call   0xd81
     e61:	75 1a                	jne    0xe7d
     e63:	8d 75 20             	lea    0x20(%di),%si
     e66:	b9 05 00             	mov    $0x5,%cx
     e69:	65 80 7c 08 04       	cmpb   $0x4,%gs:0x8(%si)
     e6e:	75 08                	jne    0xe78
     e70:	66 65 83 7c 04 00    	cmpl   $0x0,%gs:0x4(%si)
     e76:	75 08                	jne    0xe80
     e78:	83 c6 40             	add    $0x40,%si
     e7b:	e2 ec                	loop   0xe69
     e7d:	0c 01                	or     $0x1,%al
     e7f:	c3                   	ret    
     e80:	26 8a 86 e2 02       	mov    %es:0x2e2(%bp),%al
     e85:	a2 e2 1b             	mov    %al,0x1be2
     e88:	c6 06 e0 1b 01       	movb   $0x1,0x1be0
     e8d:	be 56 4e             	mov    $0x4e56,%si
     e90:	e8 66 02             	call   0x10f9
     e93:	bb 7e 00             	mov    $0x7e,%bx
     e96:	e8 30 03             	call   0x11c9
     e99:	3d 00 13             	cmp    $0x1300,%ax
     e9c:	75 0b                	jne    0xea9
     e9e:	c6 06 e1 1b 01       	movb   $0x1,0x1be1
     ea3:	be 85 4e             	mov    $0x4e85,%si
     ea6:	e8 50 02             	call   0x10f9
     ea9:	33 c0                	xor    %ax,%ax
     eab:	c3                   	ret    
     eac:	be 34 1b             	mov    $0x1b34,%si
     eaf:	e8 47 02             	call   0x10f9
     eb2:	66 26 c7 86 d0 02 00 	movl   $0x0,%es:0x2d0(%bp)
     eb9:	00 00 00 
     ebc:	66 26 c7 86 d4 02 00 	movl   $0x0,%es:0x2d4(%bp)
     ec3:	00 00 00 
     ec6:	66 26 c7 86 d8 02 00 	movl   $0x0,%es:0x2d8(%bp)
     ecd:	00 00 00 
     ed0:	66 26 c7 86 dc 02 00 	movl   $0x0,%es:0x2dc(%bp)
     ed7:	00 00 00 
     eda:	26 c6 86 d0 02 2b    	movb   $0x2b,%es:0x2d0(%bp)
     ee0:	26 c6 86 d2 02 0a    	movb   $0xa,%es:0x2d2(%bp)
     ee6:	66 26 c7 86 d8 02 00 	movl   $0x10000,%es:0x2d8(%bp)
     eed:	00 01 00 
     ef0:	a0 e2 1b             	mov    0x1be2,%al
     ef3:	26 88 86 e2 02       	mov    %al,%es:0x2e2(%bp)
     ef8:	e8 86 fe             	call   0xd81
     efb:	0f 85 94 00          	jne    0xf93
     eff:	8e 26 04 1c          	mov    0x1c04,%fs
     f03:	64 81 3e 00 00 e5 5e 	cmpw   $0x5ee5,%fs:0x0
     f0a:	0f 85 85 00          	jne    0xf93
     f0e:	be 60 1b             	mov    $0x1b60,%si
     f11:	e8 e5 01             	call   0x10f9
     f14:	66 33 c0             	xor    %eax,%eax
     f17:	8e 26 04 1c          	mov    0x1c04,%fs
     f1b:	64 a1 14 00          	mov    %fs:0x14,%ax
     f1f:	83 e8 20             	sub    $0x20,%ax
     f22:	8b f8                	mov    %ax,%di
     f24:	26 c7 86 08 03 00 00 	movw   $0x0,%es:0x308(%bp)
     f2b:	26 89 86 0a 03       	mov    %ax,%es:0x30a(%bp)
     f30:	66 c1 e0 04          	shl    $0x4,%eax
     f34:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
     f3a:	e8 44 fe             	call   0xd81
     f3d:	75 54                	jne    0xf93
     f3f:	be 8b 1b             	mov    $0x1b8b,%si
     f42:	e8 b4 01             	call   0x10f9
     f45:	26 0f b5 be 08 03    	lgs    %es:0x308(%bp),%di
     f4b:	65 8e 45 0c          	mov    %gs:0xc(%di),%es
     f4f:	65 8b 45 10          	mov    %gs:0x10(%di),%ax
     f53:	26 89 86 0c 03       	mov    %ax,%es:0x30c(%bp)
     f58:	65 8b 45 0e          	mov    %gs:0xe(%di),%ax
     f5c:	26 89 86 0e 03       	mov    %ax,%es:0x30e(%bp)
     f61:	26 0f b2 a6 0c 03    	lss    %es:0x30c(%bp),%sp
     f67:	65 8b 45 12          	mov    %gs:0x12(%di),%ax
     f6b:	26 89 86 04 03       	mov    %ax,%es:0x304(%bp)
     f70:	65 8b 45 08          	mov    %gs:0x8(%di),%ax
     f74:	26 89 86 06 03       	mov    %ax,%es:0x306(%bp)
     f79:	65 8e 5d 0a          	mov    %gs:0xa(%di),%ds
     f7d:	26 ff 9e 04 03       	lcall  *%es:0x304(%bp)
     f82:	2e 8e 26 00 1c       	mov    %cs:0x1c00,%fs
     f87:	64 c7 06 72 00 34 12 	movw   $0x1234,%fs:0x72
     f8e:	2e ff 2e 18 1c       	ljmp   *%cs:0x1c18
     f93:	be b7 1b             	mov    $0x1bb7,%si
     f96:	e8 60 01             	call   0x10f9
     f99:	0c 01                	or     $0x1,%al
     f9b:	c3                   	ret    
     f9c:	26 8a 86 bc 02       	mov    %es:0x2bc(%bp),%al
     fa1:	80 3e e4 1b 00       	cmpb   $0x0,0x1be4
     fa6:	74 15                	je     0xfbd
     fa8:	38 06 e7 1b          	cmp    %al,0x1be7
     fac:	75 0f                	jne    0xfbd
     fae:	26 c6 86 e3 02 00    	movb   $0x0,%es:0x2e3(%bp)
     fb4:	a0 e6 1b             	mov    0x1be6,%al
     fb7:	26 88 86 e2 02       	mov    %al,%es:0x2e2(%bp)
     fbc:	c3                   	ret    
     fbd:	24 7f                	and    $0x7f,%al
     fbf:	2a 06 d0 00          	sub    0xd0,%al
     fc3:	0f b6 0e 55 01       	movzbw 0x155,%cx
     fc8:	33 db                	xor    %bx,%bx
     fca:	bf d1 00             	mov    $0xd1,%di
     fcd:	8a d8                	mov    %al,%bl
     fcf:	2a 05                	sub    (%di),%al
     fd1:	72 07                	jb     0xfda
     fd3:	fe c7                	inc    %bh
     fd5:	47                   	inc    %di
     fd6:	e2 f5                	loop   0xfcd
     fd8:	f9                   	stc    
     fd9:	c3                   	ret    
     fda:	26 88 9e e3 02       	mov    %bl,%es:0x2e3(%bp)
     fdf:	26 88 be e2 02       	mov    %bh,%es:0x2e2(%bp)
     fe4:	0c 01                	or     $0x1,%al
     fe6:	c3                   	ret    
     fe7:	0f b6 c7             	movzbw %bh,%ax
     fea:	40                   	inc    %ax
     feb:	f6 e3                	mul    %bl
     fed:	66 0f b7 c8          	movzwl %ax,%ecx
     ff1:	66 26 8b 86 14 03    	mov    %es:0x314(%bp),%eax
     ff7:	66 33 d2             	xor    %edx,%edx
     ffa:	66 f7 f1             	div    %ecx
     ffd:	66 48                	dec    %eax
     fff:	66 3d fe 03 00 00    	cmp    $0x3fe,%eax
    1005:	76 03                	jbe    0x100a
    1007:	b8 fe 03             	mov    $0x3fe,%ax
    100a:	c0 e4 06             	shl    $0x6,%ah
    100d:	86 e0                	xchg   %ah,%al
    100f:	0a c3                	or     %bl,%al
    1011:	26 89 86 b8 02       	mov    %ax,%es:0x2b8(%bp)
    1016:	8a e7                	mov    %bh,%ah
    1018:	fa                   	cli    
    1019:	8e 26 00 1c          	mov    0x1c00,%fs
    101d:	64 a0 75 00          	mov    %fs:0x75,%al
    1021:	26 89 86 bc 02       	mov    %ax,%es:0x2bc(%bp)
    1026:	c3                   	ret    
    1027:	26 8b 8e b8 02       	mov    %es:0x2b8(%bp),%cx
    102c:	83 e1 3f             	and    $0x3f,%cx
    102f:	fe c9                	dec    %cl
    1031:	26 0f b6 86 bd 02    	movzbw %es:0x2bd(%bp),%ax
    1037:	f6 e3                	mul    %bl
    1039:	03 c8                	add    %ax,%cx
    103b:	26 8b 86 b8 02       	mov    %es:0x2b8(%bp),%ax
    1040:	c0 e8 06             	shr    $0x6,%al
    1043:	86 e0                	xchg   %ah,%al
    1045:	50                   	push   %ax
    1046:	0f b6 c7             	movzbw %bh,%ax
    1049:	40                   	inc    %ax
    104a:	f6 e3                	mul    %bl
    104c:	5b                   	pop    %bx
    104d:	f7 e3                	mul    %bx
    104f:	03 c1                	add    %cx,%ax
    1051:	83 d2 00             	adc    $0x0,%dx
    1054:	26 89 86 14 03       	mov    %ax,%es:0x314(%bp)
    1059:	26 89 96 16 03       	mov    %dx,%es:0x316(%bp)
    105e:	66 26 8b 86 14 03    	mov    %es:0x314(%bp),%eax
    1064:	c3                   	ret    
    1065:	66 51                	push   %ecx
    1067:	86 e0                	xchg   %ah,%al
    1069:	8b c8                	mov    %ax,%cx
    106b:	66 c1 e1 10          	shl    $0x10,%ecx
    106f:	66 c1 e8 10          	shr    $0x10,%eax
    1073:	86 e0                	xchg   %ah,%al
    1075:	66 0b c1             	or     %ecx,%eax
    1078:	66 59                	pop    %ecx
    107a:	c3                   	ret    
    107b:	66 0f b7 c0          	movzwl %ax,%eax
    107f:	66 0f b7 d2          	movzwl %dx,%edx
    1083:	66 c1 e2 04          	shl    $0x4,%edx
    1087:	66 03 c2             	add    %edx,%eax
    108a:	c3                   	ret    
    108b:	b0 2e                	mov    $0x2e,%al
    108d:	9c                   	pushf  
    108e:	50                   	push   %ax
    108f:	2e 80 3e 87 01 00    	cmpb   $0x0,%cs:0x187
    1095:	74 32                	je     0x10c9
    1097:	52                   	push   %dx
    1098:	50                   	push   %ax
    1099:	2e 8b 16 8a 01       	mov    %cs:0x18a,%dx
    109e:	e8 48 02             	call   0x12e9
    10a1:	ec                   	in     (%dx),%al
    10a2:	a8 01                	test   $0x1,%al
    10a4:	74 0c                	je     0x10b2
    10a6:	e8 40 02             	call   0x12e9
    10a9:	2e 8b 16 88 01       	mov    %cs:0x188,%dx
    10ae:	ec                   	in     (%dx),%al
    10af:	e8 09 01             	call   0x11bb
    10b2:	a8 40                	test   $0x40,%al
    10b4:	74 e3                	je     0x1099
    10b6:	e8 30 02             	call   0x12e9
    10b9:	58                   	pop    %ax
    10ba:	2e 8b 16 88 01       	mov    %cs:0x188,%dx
    10bf:	ee                   	out    %al,(%dx)
    10c0:	5a                   	pop    %dx
    10c1:	2e 80 3e 87 01 83    	cmpb   $0x83,%cs:0x187
    10c7:	77 04                	ja     0x10cd
    10c9:	b4 0e                	mov    $0xe,%ah
    10cb:	cd 10                	int    $0x10
    10cd:	58                   	pop    %ax
    10ce:	9d                   	popf   
    10cf:	c3                   	ret    
    10d0:	3c 09                	cmp    $0x9,%al
    10d2:	77 03                	ja     0x10d7
    10d4:	04 30                	add    $0x30,%al
    10d6:	c3                   	ret    
    10d7:	04 37                	add    $0x37,%al
    10d9:	c3                   	ret    
    10da:	50                   	push   %ax
    10db:	3c 09                	cmp    $0x9,%al
    10dd:	76 04                	jbe    0x10e3
    10df:	04 37                	add    $0x37,%al
    10e1:	eb 02                	jmp    0x10e5
    10e3:	04 30                	add    $0x30,%al
    10e5:	e8 a5 ff             	call   0x108d
    10e8:	58                   	pop    %ax
    10e9:	c3                   	ret    
    10ea:	50                   	push   %ax
    10eb:	56                   	push   %si
    10ec:	8a 04                	mov    (%si),%al
    10ee:	88 05                	mov    %al,(%di)
    10f0:	46                   	inc    %si
    10f1:	47                   	inc    %di
    10f2:	0a c0                	or     %al,%al
    10f4:	75 f6                	jne    0x10ec
    10f6:	5e                   	pop    %si
    10f7:	58                   	pop    %ax
    10f8:	c3                   	ret    
    10f9:	50                   	push   %ax
    10fa:	9c                   	pushf  
    10fb:	2e 8a 04             	mov    %cs:(%si),%al
    10fe:	46                   	inc    %si
    10ff:	0a c0                	or     %al,%al
    1101:	74 05                	je     0x1108
    1103:	e8 87 ff             	call   0x108d
    1106:	eb f3                	jmp    0x10fb
    1108:	9d                   	popf   
    1109:	58                   	pop    %ax
    110a:	c3                   	ret    
    110b:	56                   	push   %si
    110c:	be 4f 1a             	mov    $0x1a4f,%si
    110f:	e8 e7 ff             	call   0x10f9
    1112:	5e                   	pop    %si
    1113:	c3                   	ret    
    1114:	8a e0                	mov    %al,%ah
    1116:	c0 e8 04             	shr    $0x4,%al
    1119:	e8 b4 ff             	call   0x10d0
    111c:	86 c4                	xchg   %al,%ah
    111e:	24 0f                	and    $0xf,%al
    1120:	eb ae                	jmp    0x10d0
    1122:	50                   	push   %ax
    1123:	8a e0                	mov    %al,%ah
    1125:	c0 e8 04             	shr    $0x4,%al
    1128:	e8 af ff             	call   0x10da
    112b:	8a c4                	mov    %ah,%al
    112d:	24 0f                	and    $0xf,%al
    112f:	e8 a8 ff             	call   0x10da
    1132:	58                   	pop    %ax
    1133:	c3                   	ret    
    1134:	3c 0a                	cmp    $0xa,%al
    1136:	73 0a                	jae    0x1142
    1138:	50                   	push   %ax
    1139:	32 c0                	xor    %al,%al
    113b:	e8 92 ff             	call   0x10d0
    113e:	88 05                	mov    %al,(%di)
    1140:	47                   	inc    %di
    1141:	58                   	pop    %ax
    1142:	50                   	push   %ax
    1143:	53                   	push   %bx
    1144:	3c 64                	cmp    $0x64,%al
    1146:	72 1b                	jb     0x1163
    1148:	32 e4                	xor    %ah,%ah
    114a:	b3 64                	mov    $0x64,%bl
    114c:	f6 f3                	div    %bl
    114e:	e8 7f ff             	call   0x10d0
    1151:	88 05                	mov    %al,(%di)
    1153:	47                   	inc    %di
    1154:	80 fc 0a             	cmp    $0xa,%ah
    1157:	73 08                	jae    0x1161
    1159:	32 c0                	xor    %al,%al
    115b:	e8 72 ff             	call   0x10d0
    115e:	88 05                	mov    %al,(%di)
    1160:	47                   	inc    %di
    1161:	8a c4                	mov    %ah,%al
    1163:	3c 0a                	cmp    $0xa,%al
    1165:	72 0e                	jb     0x1175
    1167:	32 e4                	xor    %ah,%ah
    1169:	b3 0a                	mov    $0xa,%bl
    116b:	f6 f3                	div    %bl
    116d:	e8 60 ff             	call   0x10d0
    1170:	88 05                	mov    %al,(%di)
    1172:	47                   	inc    %di
    1173:	8a c4                	mov    %ah,%al
    1175:	e8 58 ff             	call   0x10d0
    1178:	88 05                	mov    %al,(%di)
    117a:	47                   	inc    %di
    117b:	5b                   	pop    %bx
    117c:	58                   	pop    %ax
    117d:	c3                   	ret    
    117e:	eb 0b                	jmp    0x118b
    1180:	3c 0a                	cmp    $0xa,%al
    1182:	73 07                	jae    0x118b
    1184:	50                   	push   %ax
    1185:	32 c0                	xor    %al,%al
    1187:	e8 50 ff             	call   0x10da
    118a:	58                   	pop    %ax
    118b:	50                   	push   %ax
    118c:	53                   	push   %bx
    118d:	3c 64                	cmp    $0x64,%al
    118f:	72 15                	jb     0x11a6
    1191:	32 e4                	xor    %ah,%ah
    1193:	b3 64                	mov    $0x64,%bl
    1195:	f6 f3                	div    %bl
    1197:	e8 40 ff             	call   0x10da
    119a:	80 fc 0a             	cmp    $0xa,%ah
    119d:	73 05                	jae    0x11a4
    119f:	32 c0                	xor    %al,%al
    11a1:	e8 36 ff             	call   0x10da
    11a4:	8a c4                	mov    %ah,%al
    11a6:	3c 0a                	cmp    $0xa,%al
    11a8:	72 0b                	jb     0x11b5
    11aa:	32 e4                	xor    %ah,%ah
    11ac:	b3 0a                	mov    $0xa,%bl
    11ae:	f6 f3                	div    %bl
    11b0:	e8 27 ff             	call   0x10da
    11b3:	8a c4                	mov    %ah,%al
    11b5:	e8 22 ff             	call   0x10da
    11b8:	5b                   	pop    %bx
    11b9:	58                   	pop    %ax
    11ba:	c3                   	ret    
    11bb:	0f b6 16 87 01       	movzbw 0x187,%dx
    11c0:	83 e2 03             	and    $0x3,%dx
    11c3:	b8 e3 00             	mov    $0xe3,%ax
    11c6:	cd 14                	int    $0x14
    11c8:	c3                   	ret    
    11c9:	fa                   	cli    
    11ca:	8e 26 00 1c          	mov    0x1c00,%fs
    11ce:	66 64 a1 6c 00       	mov    %fs:0x6c,%eax
    11d3:	66 50                	push   %eax
    11d5:	fb                   	sti    
    11d6:	b4 01                	mov    $0x1,%ah
    11d8:	cd 16                	int    $0x16
    11da:	75 10                	jne    0x11ec
    11dc:	fa                   	cli    
    11dd:	66 58                	pop    %eax
    11df:	66 50                	push   %eax
    11e1:	fb                   	sti    
    11e2:	e8 4c 27             	call   0x3931
    11e5:	77 ef                	ja     0x11d6
    11e7:	66 58                	pop    %eax
    11e9:	33 c0                	xor    %ax,%ax
    11eb:	c3                   	ret    
    11ec:	66 58                	pop    %eax
    11ee:	33 c0                	xor    %ax,%ax
    11f0:	cd 16                	int    $0x16
    11f2:	c3                   	ret    
    11f3:	b4 dd                	mov    $0xdd,%ah
    11f5:	eb 02                	jmp    0x11f9
    11f7:	b4 df                	mov    $0xdf,%ah
    11f9:	e8 12 00             	call   0x120e
    11fc:	b0 d1                	mov    $0xd1,%al
    11fe:	e6 64                	out    %al,$0x64
    1200:	e8 0b 00             	call   0x120e
    1203:	8a c4                	mov    %ah,%al
    1205:	e6 60                	out    %al,$0x60
    1207:	e8 04 00             	call   0x120e
    120a:	b0 ff                	mov    $0xff,%al
    120c:	e6 64                	out    %al,$0x64
    120e:	33 c9                	xor    %cx,%cx
    1210:	e4 64                	in     $0x64,%al
    1212:	a8 02                	test   $0x2,%al
    1214:	e0 fa                	loopne 0x1210
    1216:	c3                   	ret    
    1217:	e8 a4 00             	call   0x12be
    121a:	0f 09                	wbinvd 
    121c:	8e 26 02 1c          	mov    0x1c02,%fs
    1220:	66 b9 00 00 10 00    	mov    $0x100000,%ecx
    1226:	67 64 8b 09          	mov    %fs:(%ecx),%cx
    122a:	b8 01 00             	mov    $0x1,%ax
    122d:	64 39 0e 00 00       	cmp    %cx,%fs:0x0
    1232:	0f 85 be 00          	jne    0x12f4
    1236:	64 f7 16 00 00       	notw   %fs:0x0
    123b:	66 b9 00 00 10 00    	mov    $0x100000,%ecx
    1241:	67 64 8b 09          	mov    %fs:(%ecx),%cx
    1245:	64 39 0e 00 00       	cmp    %cx,%fs:0x0
    124a:	75 02                	jne    0x124e
    124c:	33 c0                	xor    %ax,%ax
    124e:	64 f7 16 00 00       	notw   %fs:0x0
    1253:	e9 9e 00             	jmp    0x12f4
    1256:	66 33 c0             	xor    %eax,%eax
    1259:	8c c0                	mov    %es,%ax
    125b:	66 c1 e0 04          	shl    $0x4,%eax
    125f:	66 0f b7 ed          	movzwl %bp,%ebp
    1263:	66 03 c5             	add    %ebp,%eax
    1266:	66 83 c0 00          	add    $0x0,%eax
    126a:	66 26 89 46 22       	mov    %eax,%es:0x22(%bp)
    126f:	66 26 c7 46 10 ff ff 	movl   $0xffff,%es:0x10(%bp)
    1276:	00 00 
    1278:	66 26 c7 46 14 00 92 	movl   $0xcf9200,%es:0x14(%bp)
    127f:	cf 00 
    1281:	26 c7 46 20 17 00    	movw   $0x17,%es:0x20(%bp)
    1287:	c3                   	ret    
    1288:	9c                   	pushf  
    1289:	fa                   	cli    
    128a:	e8 c9 ff             	call   0x1256
    128d:	66 26 0f 01 46 28    	sgdtl  %es:0x28(%bp)
    1293:	66 26 0f 01 56 20    	lgdtl  %es:0x20(%bp)
    1299:	0f 20 c0             	mov    %cr0,%eax
    129c:	0c 01                	or     $0x1,%al
    129e:	0f 22 c0             	mov    %eax,%cr0
    12a1:	eb 00                	jmp    0x12a3
    12a3:	b8 10 00             	mov    $0x10,%ax
    12a6:	8e e0                	mov    %ax,%fs
    12a8:	0f 20 c0             	mov    %cr0,%eax
    12ab:	24 fe                	and    $0xfe,%al
    12ad:	0f 22 c0             	mov    %eax,%cr0
    12b0:	eb 00                	jmp    0x12b2
    12b2:	8e 26 02 1c          	mov    0x1c02,%fs
    12b6:	66 26 0f 01 56 28    	lgdtl  %es:0x28(%bp)
    12bc:	9d                   	popf   
    12bd:	c3                   	ret    
    12be:	f0 66 26 83 86 b0 02 	lock addl $0x0,%es:0x2b0(%bp)
    12c5:	00 
    12c6:	66 50                	push   %eax
    12c8:	9c                   	pushf  
    12c9:	fa                   	cli    
    12ca:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    12d0:	75 03                	jne    0x12d5
    12d2:	e8 b3 ff             	call   0x1288
    12d5:	8e 26 02 1c          	mov    0x1c02,%fs
    12d9:	0f 20 c0             	mov    %cr0,%eax
    12dc:	66 0d 00 00 00 40    	or     $0x40000000,%eax
    12e2:	0f 22 c0             	mov    %eax,%cr0
    12e5:	9d                   	popf   
    12e6:	66 58                	pop    %eax
    12e8:	c3                   	ret    
    12e9:	51                   	push   %cx
    12ea:	b9 00 02             	mov    $0x200,%cx
    12ed:	e8 03 00             	call   0x12f3
    12f0:	e2 fb                	loop   0x12ed
    12f2:	59                   	pop    %cx
    12f3:	c3                   	ret    
    12f4:	f0 66 26 83 86 b0 02 	lock addl $0x0,%es:0x2b0(%bp)
    12fb:	00 
    12fc:	66 50                	push   %eax
    12fe:	66 26 8b 86 ec 02    	mov    %es:0x2ec(%bp),%eax
    1304:	0f 22 c0             	mov    %eax,%cr0
    1307:	66 58                	pop    %eax
    1309:	c3                   	ret    
    130a:	fa                   	cli    
    130b:	66 b8 01 00 00 00    	mov    $0x1,%eax
    1311:	0f 20 c0             	mov    %cr0,%eax
    1314:	66 26 89 86 ec 02    	mov    %eax,%es:0x2ec(%bp)
    131a:	a8 01                	test   $0x1,%al
    131c:	75 0f                	jne    0x132d
    131e:	e8 67 ff             	call   0x1288
    1321:	b0 01                	mov    $0x1,%al
    1323:	26 88 86 e9 02       	mov    %al,%es:0x2e9(%bp)
    1328:	3c 00                	cmp    $0x0,%al
    132a:	e8 ca fe             	call   0x11f7
    132d:	c3                   	ret    
    132e:	66 33 c0             	xor    %eax,%eax
    1331:	66 81 fa 00 00 01 00 	cmp    $0x10000,%edx
    1338:	72 13                	jb     0x134d
    133a:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    1340:	0f 85 b8 00          	jne    0x13fc
    1344:	e8 77 ff             	call   0x12be
    1347:	67 64 8a 02          	mov    %fs:(%edx),%al
    134b:	eb a7                	jmp    0x12f4
    134d:	ec                   	in     (%dx),%al
    134e:	eb 99                	jmp    0x12e9
    1350:	66 33 c0             	xor    %eax,%eax
    1353:	66 81 fa 00 00 01 00 	cmp    $0x10000,%edx
    135a:	72 13                	jb     0x136f
    135c:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    1362:	0f 85 c1 00          	jne    0x1427
    1366:	e8 55 ff             	call   0x12be
    1369:	67 64 8b 02          	mov    %fs:(%edx),%ax
    136d:	eb 85                	jmp    0x12f4
    136f:	ed                   	in     (%dx),%ax
    1370:	e9 76 ff             	jmp    0x12e9
    1373:	66 33 c0             	xor    %eax,%eax
    1376:	66 81 fa 00 00 01 00 	cmp    $0x10000,%edx
    137d:	72 15                	jb     0x1394
    137f:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    1385:	0f 85 a4 00          	jne    0x142d
    1389:	e8 32 ff             	call   0x12be
    138c:	67 66 64 8b 02       	mov    %fs:(%edx),%eax
    1391:	e9 60 ff             	jmp    0x12f4
    1394:	66 ed                	in     (%dx),%eax
    1396:	e9 50 ff             	jmp    0x12e9
    1399:	66 81 fa 00 00 01 00 	cmp    $0x10000,%edx
    13a0:	72 14                	jb     0x13b6
    13a2:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    13a8:	0f 85 93 00          	jne    0x143f
    13ac:	e8 0f ff             	call   0x12be
    13af:	67 64 88 02          	mov    %al,%fs:(%edx)
    13b3:	e9 3e ff             	jmp    0x12f4
    13b6:	ee                   	out    %al,(%dx)
    13b7:	e9 2f ff             	jmp    0x12e9
    13ba:	66 81 fa 00 00 01 00 	cmp    $0x10000,%edx
    13c1:	72 14                	jb     0x13d7
    13c3:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    13c9:	0f 85 93 00          	jne    0x1460
    13cd:	e8 ee fe             	call   0x12be
    13d0:	67 64 89 02          	mov    %ax,%fs:(%edx)
    13d4:	e9 1d ff             	jmp    0x12f4
    13d7:	ef                   	out    %ax,(%dx)
    13d8:	e9 0e ff             	jmp    0x12e9
    13db:	66 81 fa 00 00 01 00 	cmp    $0x10000,%edx
    13e2:	72 13                	jb     0x13f7
    13e4:	26 f6 86 ec 02 01    	testb  $0x1,%es:0x2ec(%bp)
    13ea:	75 7a                	jne    0x1466
    13ec:	e8 cf fe             	call   0x12be
    13ef:	67 66 64 89 02       	mov    %eax,%fs:(%edx)
    13f4:	e9 fd fe             	jmp    0x12f4
    13f7:	66 ef                	out    %eax,(%dx)
    13f9:	e9 ed fe             	jmp    0x12e9
    13fc:	51                   	push   %cx
    13fd:	e8 78 00             	call   0x1478
    1400:	b9 02 00             	mov    $0x2,%cx
    1403:	f6 c2 01             	test   $0x1,%dl
    1406:	75 0c                	jne    0x1414
    1408:	e8 9f 00             	call   0x14aa
    140b:	66 26 0f b6 86 a0 02 	movzbl %es:0x2a0(%bp),%eax
    1412:	59                   	pop    %cx
    1413:	c3                   	ret    
    1414:	66 52                	push   %edx
    1416:	80 e2 fe             	and    $0xfe,%dl
    1419:	e8 8e 00             	call   0x14aa
    141c:	66 26 0f b6 86 a1 02 	movzbl %es:0x2a1(%bp),%eax
    1423:	66 5a                	pop    %edx
    1425:	59                   	pop    %cx
    1426:	c3                   	ret    
    1427:	51                   	push   %cx
    1428:	b9 02 00             	mov    $0x2,%cx
    142b:	eb 04                	jmp    0x1431
    142d:	51                   	push   %cx
    142e:	b9 04 00             	mov    $0x4,%cx
    1431:	e8 44 00             	call   0x1478
    1434:	e8 73 00             	call   0x14aa
    1437:	66 26 8b 86 a0 02    	mov    %es:0x2a0(%bp),%eax
    143d:	59                   	pop    %cx
    143e:	c3                   	ret    
    143f:	51                   	push   %cx
    1440:	b9 02 00             	mov    $0x2,%cx
    1443:	66 0f b6 c0          	movzbl %al,%eax
    1447:	f6 c2 01             	test   $0x1,%dl
    144a:	74 1e                	je     0x146a
    144c:	66 52                	push   %edx
    144e:	80 e2 fe             	and    $0xfe,%dl
    1451:	e8 24 00             	call   0x1478
    1454:	26 88 86 a1 02       	mov    %al,%es:0x2a1(%bp)
    1459:	e8 32 00             	call   0x148e
    145c:	66 5a                	pop    %edx
    145e:	59                   	pop    %cx
    145f:	c3                   	ret    
    1460:	51                   	push   %cx
    1461:	b9 02 00             	mov    $0x2,%cx
    1464:	eb 04                	jmp    0x146a
    1466:	51                   	push   %cx
    1467:	b9 04 00             	mov    $0x4,%cx
    146a:	e8 0b 00             	call   0x1478
    146d:	66 26 89 86 a0 02    	mov    %eax,%es:0x2a0(%bp)
    1473:	e8 18 00             	call   0x148e
    1476:	59                   	pop    %cx
    1477:	c3                   	ret    
    1478:	51                   	push   %cx
    1479:	57                   	push   %di
    147a:	33 ff                	xor    %di,%di
    147c:	b9 20 00             	mov    $0x20,%cx
    147f:	26 c7 83 70 02 00 00 	movw   $0x0,%es:0x270(%bp,%di)
    1486:	83 c7 02             	add    $0x2,%di
    1489:	e2 f4                	loop   0x147f
    148b:	5f                   	pop    %di
    148c:	59                   	pop    %cx
    148d:	c3                   	ret    
    148e:	66 50                	push   %eax
    1490:	66 52                	push   %edx
    1492:	8c c2                	mov    %es,%dx
    1494:	8d 86 a0 02          	lea    0x2a0(%bp),%ax
    1498:	e8 e0 fb             	call   0x107b
    149b:	66 8b d0             	mov    %eax,%edx
    149e:	66 58                	pop    %eax
    14a0:	66 50                	push   %eax
    14a2:	e8 12 00             	call   0x14b7
    14a5:	66 5a                	pop    %edx
    14a7:	66 58                	pop    %eax
    14a9:	c3                   	ret    
    14aa:	66 52                	push   %edx
    14ac:	8c c2                	mov    %es,%dx
    14ae:	8d 86 a0 02          	lea    0x2a0(%bp),%ax
    14b2:	e8 c6 fb             	call   0x107b
    14b5:	66 5a                	pop    %edx
    14b7:	66 26 89 86 8a 02    	mov    %eax,%es:0x28a(%bp)
    14bd:	66 c1 e8 18          	shr    $0x18,%eax
    14c1:	26 88 86 8f 02       	mov    %al,%es:0x28f(%bp)
    14c6:	66 8b c2             	mov    %edx,%eax
    14c9:	66 26 89 86 82 02    	mov    %eax,%es:0x282(%bp)
    14cf:	66 c1 e8 18          	shr    $0x18,%eax
    14d3:	26 88 86 87 02       	mov    %al,%es:0x287(%bp)
    14d8:	26 c6 86 85 02 93    	movb   $0x93,%es:0x285(%bp)
    14de:	26 c6 86 8d 02 93    	movb   $0x93,%es:0x28d(%bp)
    14e4:	26 89 8e 80 02       	mov    %cx,%es:0x280(%bp)
    14e9:	26 89 8e 88 02       	mov    %cx,%es:0x288(%bp)
    14ee:	b4 87                	mov    $0x87,%ah
    14f0:	d1 e9                	shr    %cx
    14f2:	56                   	push   %si
    14f3:	8d b6 70 02          	lea    0x270(%bp),%si
    14f7:	cd 15                	int    $0x15
    14f9:	73 09                	jae    0x1504
    14fb:	be 52 1a             	mov    $0x1a52,%si
    14fe:	e8 f8 fb             	call   0x10f9
    1501:	e8 ea fc             	call   0x11ee
    1504:	5e                   	pop    %si
    1505:	c3                   	ret    
    1506:	66 ba 20 00 00 00    	mov    $0x20,%edx
    150c:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    1512:	e9 19 fe             	jmp    0x132e
    1515:	b0 02                	mov    $0x2,%al
    1517:	66 ba 20 00 00 00    	mov    $0x20,%edx
    151d:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    1523:	e9 73 fe             	jmp    0x1399
    1526:	66 ba 2c 00 00 00    	mov    $0x2c,%edx
    152c:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    1532:	e9 f9 fd             	jmp    0x132e
    1535:	66 ba 2c 00 00 00    	mov    $0x2c,%edx
    153b:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    1541:	e9 55 fe             	jmp    0x1399
    1544:	66 ba 3f 10 00 00    	mov    $0x103f,%edx
    154a:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    1550:	e9 db fd             	jmp    0x132e
    1553:	66 ba 3f 10 00 00    	mov    $0x103f,%edx
    1559:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    155f:	e9 37 fe             	jmp    0x1399
    1562:	66 ba 34 00 00 00    	mov    $0x34,%edx
    1568:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    156e:	e9 bd fd             	jmp    0x132e
    1571:	b0 ff                	mov    $0xff,%al
    1573:	66 ba 34 00 00 00    	mov    $0x34,%edx
    1579:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    157f:	e9 17 fe             	jmp    0x1399
    1582:	51                   	push   %cx
    1583:	b9 00 10             	mov    $0x1000,%cx
    1586:	e8 7d ff             	call   0x1506
    1589:	a8 01                	test   $0x1,%al
    158b:	74 0d                	je     0x159a
    158d:	e8 59 fd             	call   0x12e9
    1590:	e2 f4                	loop   0x1586
    1592:	56                   	push   %si
    1593:	be 3e 52             	mov    $0x523e,%si
    1596:	e8 60 fb             	call   0x10f9
    1599:	5e                   	pop    %si
    159a:	59                   	pop    %cx
    159b:	c3                   	ret    
    159c:	66 ba 18 10 00 00    	mov    $0x1018,%edx
    15a2:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    15a8:	e8 c8 fd             	call   0x1373
    15ab:	66 50                	push   %eax
    15ad:	b0 01                	mov    $0x1,%al
    15af:	e8 83 ff             	call   0x1535
    15b2:	e8 60 ff             	call   0x1515
    15b5:	66 58                	pop    %eax
    15b7:	66 c1 e8 10          	shr    $0x10,%eax
    15bb:	c3                   	ret    
    15bc:	66 ba 00 10 00 00    	mov    $0x1000,%edx
    15c2:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    15c8:	66 26 8b 86 d0 02    	mov    %es:0x2d0(%bp),%eax
    15ce:	e8 0a fe             	call   0x13db
    15d1:	66 26 8b 86 d4 02    	mov    %es:0x2d4(%bp),%eax
    15d7:	66 83 c2 04          	add    $0x4,%edx
    15db:	e8 fd fd             	call   0x13db
    15de:	66 26 8b 86 d8 02    	mov    %es:0x2d8(%bp),%eax
    15e4:	66 83 c2 04          	add    $0x4,%edx
    15e8:	e8 f0 fd             	call   0x13db
    15eb:	66 26 8b 86 dc 02    	mov    %es:0x2dc(%bp),%eax
    15f1:	66 83 c2 04          	add    $0x4,%edx
    15f5:	e8 e3 fd             	call   0x13db
    15f8:	b0 01                	mov    $0x1,%al
    15fa:	e9 1a ff             	jmp    0x1517
    15fd:	66 60                	pushal 
    15ff:	0f a8                	push   %gs
    1601:	0f a0                	push   %fs
    1603:	06                   	push   %es
    1604:	1e                   	push   %ds
    1605:	0e                   	push   %cs
    1606:	1f                   	pop    %ds
    1607:	80 3e e9 1b 00       	cmpb   $0x0,0x1be9
    160c:	75 74                	jne    0x1682
    160e:	2e a1 fe 1b          	mov    %cs:0x1bfe,%ax
    1612:	2e 8e 06 00 1c       	mov    %cs:0x1c00,%es
    1617:	26 03 06 0e 00       	add    %es:0xe,%ax
    161c:	8e c0                	mov    %ax,%es
    161e:	66 33 ed             	xor    %ebp,%ebp
    1621:	e8 e6 fc             	call   0x130a
    1624:	bb ff ff             	mov    $0xffff,%bx
    1627:	66 26 ff b6 e4 02    	pushl  %es:0x2e4(%bp)
    162d:	43                   	inc    %bx
    162e:	3a 1e 55 01          	cmp    0x155,%bl
    1632:	73 48                	jae    0x167c
    1634:	c1 e3 02             	shl    $0x2,%bx
    1637:	66 8b 87 10 01       	mov    0x110(%bx),%eax
    163c:	c1 eb 02             	shr    $0x2,%bx
    163f:	66 26 89 86 e4 02    	mov    %eax,%es:0x2e4(%bp)
    1645:	e8 1a ff             	call   0x1562
    1648:	3c ff                	cmp    $0xff,%al
    164a:	74 e1                	je     0x162d
    164c:	e8 d7 fe             	call   0x1526
    164f:	24 01                	and    $0x1,%al
    1651:	74 da                	je     0x162d
    1653:	e8 1b ff             	call   0x1571
    1656:	d1 e3                	shl    %bx
    1658:	b0 20                	mov    $0x20,%al
    165a:	80 bf f0 00 ff       	cmpb   $0xff,0xf0(%bx)
    165f:	74 02                	je     0x1663
    1661:	e6 a0                	out    %al,$0xa0
    1663:	e6 20                	out    %al,$0x20
    1665:	b8 00 91             	mov    $0x9100,%ax
    1668:	cd 15                	int    $0x15
    166a:	66 26 8f 86 e4 02    	popl   %es:0x2e4(%bp)
    1670:	1f                   	pop    %ds
    1671:	07                   	pop    %es
    1672:	0f a1                	pop    %fs
    1674:	0f a9                	pop    %gs
    1676:	66 61                	popal  
    1678:	83 c4 04             	add    $0x4,%sp
    167b:	cf                   	iret   
    167c:	66 26 8f 86 e4 02    	popl   %es:0x2e4(%bp)
    1682:	1f                   	pop    %ds
    1683:	07                   	pop    %es
    1684:	0f a1                	pop    %fs
    1686:	0f a9                	pop    %gs
    1688:	66 61                	popal  
    168a:	cb                   	lret   
    168b:	66 2e ff 36 40 00    	pushl  %cs:0x40
    1691:	e9 69 ff             	jmp    0x15fd
    1694:	66 2e ff 36 44 00    	pushl  %cs:0x44
    169a:	e9 60 ff             	jmp    0x15fd
    169d:	66 2e ff 36 48 00    	pushl  %cs:0x48
    16a3:	e9 57 ff             	jmp    0x15fd
    16a6:	66 2e ff 36 4c 00    	pushl  %cs:0x4c
    16ac:	e9 4e ff             	jmp    0x15fd
    16af:	66 2e ff 36 50 00    	pushl  %cs:0x50
    16b5:	e9 45 ff             	jmp    0x15fd
    16b8:	66 2e ff 36 54 00    	pushl  %cs:0x54
    16be:	e9 3c ff             	jmp    0x15fd
    16c1:	66 2e ff 36 58 00    	pushl  %cs:0x58
    16c7:	e9 33 ff             	jmp    0x15fd
    16ca:	66 2e ff 36 5c 00    	pushl  %cs:0x5c
    16d0:	e9 2a ff             	jmp    0x15fd
    16d3:	66 2e ff 36 60 00    	pushl  %cs:0x60
    16d9:	e9 21 ff             	jmp    0x15fd
    16dc:	66 2e ff 36 64 00    	pushl  %cs:0x64
    16e2:	e9 18 ff             	jmp    0x15fd
    16e5:	66 2e ff 36 68 00    	pushl  %cs:0x68
    16eb:	e9 0f ff             	jmp    0x15fd
    16ee:	66 2e ff 36 6c 00    	pushl  %cs:0x6c
    16f4:	e9 06 ff             	jmp    0x15fd
    16f7:	66 2e ff 36 70 00    	pushl  %cs:0x70
    16fd:	e9 fd fe             	jmp    0x15fd
    1700:	66 2e ff 36 74 00    	pushl  %cs:0x74
    1706:	e9 f4 fe             	jmp    0x15fd
    1709:	66 2e ff 36 78 00    	pushl  %cs:0x78
    170f:	e9 eb fe             	jmp    0x15fd
    1712:	66 2e ff 36 7c 00    	pushl  %cs:0x7c
    1718:	e9 e2 fe             	jmp    0x15fd
    171b:	66 26 0f b6 86 f4 02 	movzbl %es:0x2f4(%bp),%eax
    1722:	66 c1 e0 09          	shl    $0x9,%eax
    1726:	66 26 89 46 30       	mov    %eax,%es:0x30(%bp)
    172b:	66 26 0f b7 86 f8 02 	movzwl %es:0x2f8(%bp),%eax
    1732:	66 26 89 46 34       	mov    %eax,%es:0x34(%bp)
    1737:	66 26 0f b7 86 fa 02 	movzwl %es:0x2fa(%bp),%eax
    173e:	66 26 89 46 38       	mov    %eax,%es:0x38(%bp)
    1743:	26 c7 46 3e 00 00    	movw   $0x0,%es:0x3e(%bp)
    1749:	ba 00 00             	mov    $0x0,%dx
    174c:	b8 05 81             	mov    $0x8105,%ax
    174f:	8d 7e 30             	lea    0x30(%bp),%di
    1752:	cd 4b                	int    $0x4b
    1754:	72 09                	jb     0x175f
    1756:	c3                   	ret    
    1757:	ba 00 00             	mov    $0x0,%dx
    175a:	b8 06 81             	mov    $0x8106,%ax
    175d:	eb f0                	jmp    0x174f
    175f:	be ab 1a             	mov    $0x1aab,%si
    1762:	e8 94 f9             	call   0x10f9
    1765:	eb fe                	jmp    0x1765
    1767:	9c                   	pushf  
    1768:	50                   	push   %ax
    1769:	56                   	push   %si
    176a:	be 0b 1b             	mov    $0x1b0b,%si
    176d:	e8 89 f9             	call   0x10f9
    1770:	e8 7b fa             	call   0x11ee
    1773:	5e                   	pop    %si
    1774:	58                   	pop    %ax
    1775:	9d                   	popf   
    1776:	c3                   	ret    
    1777:	9c                   	pushf  
    1778:	16                   	push   %ss
    1779:	54                   	push   %sp
    177a:	5f                   	pop    %di
    177b:	0f a1                	pop    %fs
    177d:	e8 1d 01             	call   0x189d
    1780:	e8 9c 00             	call   0x181f
    1783:	e8 85 f9             	call   0x110b
    1786:	b9 05 00             	mov    $0x5,%cx
    1789:	64 8b 15             	mov    %fs:(%di),%dx
    178c:	e8 90 00             	call   0x181f
    178f:	e8 78 00             	call   0x180a
    1792:	e8 76 f9             	call   0x110b
    1795:	83 c7 02             	add    $0x2,%di
    1798:	e2 ef                	loop   0x1789
    179a:	9d                   	popf   
    179b:	c3                   	ret    
    179c:	20 41 58             	and    %al,0x58(%bx,%di)
    179f:	3d 00 56             	cmp    $0x5600,%ax
    17a2:	50                   	push   %ax
    17a3:	8b c0                	mov    %ax,%ax
    17a5:	be 9c 17             	mov    $0x179c,%si
    17a8:	e8 4e f9             	call   0x10f9
    17ab:	e8 e4 01             	call   0x1992
    17ae:	58                   	pop    %ax
    17af:	5e                   	pop    %si
    17b0:	c3                   	ret    
    17b1:	20 53 50             	and    %dl,0x50(%bp,%di)
    17b4:	3d 00 56             	cmp    $0x5600,%ax
    17b7:	50                   	push   %ax
    17b8:	8b c4                	mov    %sp,%ax
    17ba:	be b1 17             	mov    $0x17b1,%si
    17bd:	e8 39 f9             	call   0x10f9
    17c0:	e8 cf 01             	call   0x1992
    17c3:	58                   	pop    %ax
    17c4:	5e                   	pop    %si
    17c5:	c3                   	ret    
    17c6:	20 42 50             	and    %al,0x50(%bp,%si)
    17c9:	3d 00 56             	cmp    $0x5600,%ax
    17cc:	50                   	push   %ax
    17cd:	8b c5                	mov    %bp,%ax
    17cf:	be c6 17             	mov    $0x17c6,%si
    17d2:	e8 24 f9             	call   0x10f9
    17d5:	e8 ba 01             	call   0x1992
    17d8:	58                   	pop    %ax
    17d9:	5e                   	pop    %si
    17da:	c3                   	ret    
    17db:	20 42 58             	and    %al,0x58(%bp,%si)
    17de:	3d 00 56             	cmp    $0x5600,%ax
    17e1:	50                   	push   %ax
    17e2:	8b c3                	mov    %bx,%ax
    17e4:	be db 17             	mov    $0x17db,%si
    17e7:	e8 0f f9             	call   0x10f9
    17ea:	e8 a5 01             	call   0x1992
    17ed:	58                   	pop    %ax
    17ee:	5e                   	pop    %si
    17ef:	c3                   	ret    
    17f0:	20 43 58             	and    %al,0x58(%bp,%di)
    17f3:	3d 00 56             	cmp    $0x5600,%ax
    17f6:	50                   	push   %ax
    17f7:	8b c1                	mov    %cx,%ax
    17f9:	be f0 17             	mov    $0x17f0,%si
    17fc:	e8 fa f8             	call   0x10f9
    17ff:	e8 90 01             	call   0x1992
    1802:	58                   	pop    %ax
    1803:	5e                   	pop    %si
    1804:	c3                   	ret    
    1805:	20 44 58             	and    %al,0x58(%si)
    1808:	3d 00 56             	cmp    $0x5600,%ax
    180b:	50                   	push   %ax
    180c:	8b c2                	mov    %dx,%ax
    180e:	be 05 18             	mov    $0x1805,%si
    1811:	e8 e5 f8             	call   0x10f9
    1814:	e8 7b 01             	call   0x1992
    1817:	58                   	pop    %ax
    1818:	5e                   	pop    %si
    1819:	c3                   	ret    
    181a:	20 44 49             	and    %al,0x49(%si)
    181d:	3d 00 56             	cmp    $0x5600,%ax
    1820:	50                   	push   %ax
    1821:	8b c7                	mov    %di,%ax
    1823:	be 1a 18             	mov    $0x181a,%si
    1826:	e8 d0 f8             	call   0x10f9
    1829:	e8 66 01             	call   0x1992
    182c:	58                   	pop    %ax
    182d:	5e                   	pop    %si
    182e:	c3                   	ret    
    182f:	20 53 49             	and    %dl,0x49(%bp,%di)
    1832:	3d 00 56             	cmp    $0x5600,%ax
    1835:	50                   	push   %ax
    1836:	8b c6                	mov    %si,%ax
    1838:	be 2f 18             	mov    $0x182f,%si
    183b:	e8 bb f8             	call   0x10f9
    183e:	e8 51 01             	call   0x1992
    1841:	58                   	pop    %ax
    1842:	5e                   	pop    %si
    1843:	c3                   	ret    
    1844:	20 45 53             	and    %al,0x53(%di)
    1847:	3d 00 56             	cmp    $0x5600,%ax
    184a:	50                   	push   %ax
    184b:	8c c0                	mov    %es,%ax
    184d:	be 44 18             	mov    $0x1844,%si
    1850:	e8 a6 f8             	call   0x10f9
    1853:	e8 3c 01             	call   0x1992
    1856:	58                   	pop    %ax
    1857:	5e                   	pop    %si
    1858:	c3                   	ret    
    1859:	20 44 53             	and    %al,0x53(%si)
    185c:	3d 00 56             	cmp    $0x5600,%ax
    185f:	50                   	push   %ax
    1860:	8c d8                	mov    %ds,%ax
    1862:	be 59 18             	mov    $0x1859,%si
    1865:	e8 91 f8             	call   0x10f9
    1868:	e8 27 01             	call   0x1992
    186b:	58                   	pop    %ax
    186c:	5e                   	pop    %si
    186d:	c3                   	ret    
    186e:	20 53 53             	and    %dl,0x53(%bp,%di)
    1871:	3d 00 56             	cmp    $0x5600,%ax
    1874:	50                   	push   %ax
    1875:	8c d0                	mov    %ss,%ax
    1877:	be 6e 18             	mov    $0x186e,%si
    187a:	e8 7c f8             	call   0x10f9
    187d:	e8 12 01             	call   0x1992
    1880:	58                   	pop    %ax
    1881:	5e                   	pop    %si
    1882:	c3                   	ret    
    1883:	20 47 53             	and    %al,0x53(%bx)
    1886:	3d 00 56             	cmp    $0x5600,%ax
    1889:	50                   	push   %ax
    188a:	8c e8                	mov    %gs,%ax
    188c:	be 83 18             	mov    $0x1883,%si
    188f:	e8 67 f8             	call   0x10f9
    1892:	e8 fd 00             	call   0x1992
    1895:	58                   	pop    %ax
    1896:	5e                   	pop    %si
    1897:	c3                   	ret    
    1898:	20 46 53             	and    %al,0x53(%bp)
    189b:	3d 00 56             	cmp    $0x5600,%ax
    189e:	50                   	push   %ax
    189f:	8c e0                	mov    %fs,%ax
    18a1:	be 98 18             	mov    $0x1898,%si
    18a4:	e8 52 f8             	call   0x10f9
    18a7:	e8 e8 00             	call   0x1992
    18aa:	58                   	pop    %ax
    18ab:	5e                   	pop    %si
    18ac:	c3                   	ret    
    18ad:	20 45 41             	and    %al,0x41(%di)
    18b0:	58                   	pop    %ax
    18b1:	3d 00 66             	cmp    $0x6600,%ax
    18b4:	56                   	push   %si
    18b5:	66 50                	push   %eax
    18b7:	66 8b c0             	mov    %eax,%eax
    18ba:	be ad 18             	mov    $0x18ad,%si
    18bd:	e8 39 f8             	call   0x10f9
    18c0:	e8 c2 00             	call   0x1985
    18c3:	66 58                	pop    %eax
    18c5:	66 5e                	pop    %esi
    18c7:	c3                   	ret    
    18c8:	20 45 42             	and    %al,0x42(%di)
    18cb:	58                   	pop    %ax
    18cc:	3d 00 66             	cmp    $0x6600,%ax
    18cf:	56                   	push   %si
    18d0:	66 50                	push   %eax
    18d2:	66 8b c3             	mov    %ebx,%eax
    18d5:	be c8 18             	mov    $0x18c8,%si
    18d8:	e8 1e f8             	call   0x10f9
    18db:	e8 a7 00             	call   0x1985
    18de:	66 58                	pop    %eax
    18e0:	66 5e                	pop    %esi
    18e2:	c3                   	ret    
    18e3:	20 45 43             	and    %al,0x43(%di)
    18e6:	58                   	pop    %ax
    18e7:	3d 00 66             	cmp    $0x6600,%ax
    18ea:	56                   	push   %si
    18eb:	66 50                	push   %eax
    18ed:	66 8b c1             	mov    %ecx,%eax
    18f0:	be e3 18             	mov    $0x18e3,%si
    18f3:	e8 03 f8             	call   0x10f9
    18f6:	e8 8c 00             	call   0x1985
    18f9:	66 58                	pop    %eax
    18fb:	66 5e                	pop    %esi
    18fd:	c3                   	ret    
    18fe:	20 45 44             	and    %al,0x44(%di)
    1901:	58                   	pop    %ax
    1902:	3d 00 66             	cmp    $0x6600,%ax
    1905:	56                   	push   %si
    1906:	66 50                	push   %eax
    1908:	66 8b c2             	mov    %edx,%eax
    190b:	be fe 18             	mov    $0x18fe,%si
    190e:	e8 e8 f7             	call   0x10f9
    1911:	e8 71 00             	call   0x1985
    1914:	66 58                	pop    %eax
    1916:	66 5e                	pop    %esi
    1918:	c3                   	ret    
    1919:	20 45 44             	and    %al,0x44(%di)
    191c:	49                   	dec    %cx
    191d:	3d 00 66             	cmp    $0x6600,%ax
    1920:	56                   	push   %si
    1921:	66 50                	push   %eax
    1923:	66 8b c7             	mov    %edi,%eax
    1926:	be 19 19             	mov    $0x1919,%si
    1929:	e8 cd f7             	call   0x10f9
    192c:	e8 56 00             	call   0x1985
    192f:	66 58                	pop    %eax
    1931:	66 5e                	pop    %esi
    1933:	c3                   	ret    
    1934:	20 45 53             	and    %al,0x53(%di)
    1937:	49                   	dec    %cx
    1938:	3d 00 66             	cmp    $0x6600,%ax
    193b:	56                   	push   %si
    193c:	66 50                	push   %eax
    193e:	66 8b c6             	mov    %esi,%eax
    1941:	be 34 19             	mov    $0x1934,%si
    1944:	e8 b2 f7             	call   0x10f9
    1947:	e8 3b 00             	call   0x1985
    194a:	66 58                	pop    %eax
    194c:	66 5e                	pop    %esi
    194e:	c3                   	ret    
    194f:	20 45 42             	and    %al,0x42(%di)
    1952:	50                   	push   %ax
    1953:	3d 00 66             	cmp    $0x6600,%ax
    1956:	56                   	push   %si
    1957:	66 50                	push   %eax
    1959:	66 8b c5             	mov    %ebp,%eax
    195c:	be 4f 19             	mov    $0x194f,%si
    195f:	e8 97 f7             	call   0x10f9
    1962:	e8 20 00             	call   0x1985
    1965:	66 58                	pop    %eax
    1967:	66 5e                	pop    %esi
    1969:	c3                   	ret    
    196a:	20 45 53             	and    %al,0x53(%di)
    196d:	50                   	push   %ax
    196e:	3d 00 66             	cmp    $0x6600,%ax
    1971:	56                   	push   %si
    1972:	66 50                	push   %eax
    1974:	66 8b c4             	mov    %esp,%eax
    1977:	be 6a 19             	mov    $0x196a,%si
    197a:	e8 7c f7             	call   0x10f9
    197d:	e8 05 00             	call   0x1985
    1980:	66 58                	pop    %eax
    1982:	66 5e                	pop    %esi
    1984:	c3                   	ret    
    1985:	9c                   	pushf  
    1986:	66 50                	push   %eax
    1988:	66 c1 e8 10          	shr    $0x10,%eax
    198c:	e8 03 00             	call   0x1992
    198f:	66 58                	pop    %eax
    1991:	9d                   	popf   
    1992:	9c                   	pushf  
    1993:	86 c4                	xchg   %al,%ah
    1995:	e8 8a f7             	call   0x1122
    1998:	86 c4                	xchg   %al,%ah
    199a:	e8 85 f7             	call   0x1122
    199d:	9d                   	popf   
    199e:	c3                   	ret    
    199f:	e8 11 ff             	call   0x18b3
    19a2:	e8 29 ff             	call   0x18ce
    19a5:	e8 41 ff             	call   0x18e9
    19a8:	e8 59 ff             	call   0x1904
    19ab:	e8 8c ff             	call   0x193a
    19ae:	e8 6e ff             	call   0x191f
    19b1:	e8 a1 ff             	call   0x1955
    19b4:	e8 b9 ff             	call   0x1970
    19b7:	e8 b9 fe             	call   0x1873
    19ba:	e8 a1 fe             	call   0x185e
    19bd:	e8 89 fe             	call   0x1849
    19c0:	e8 da fe             	call   0x189d
    19c3:	e8 c2 fe             	call   0x1888
    19c6:	e9 42 f7             	jmp    0x110b
    19c9:	9c                   	pushf  
    19ca:	e8 3e f7             	call   0x110b
    19cd:	66 50                	push   %eax
    19cf:	66 26 8b 86 b0 02    	mov    %es:0x2b0(%bp),%eax
    19d5:	e8 db fe             	call   0x18b3
    19d8:	66 58                	pop    %eax
    19da:	66 53                	push   %ebx
    19dc:	66 26 8b 9e b4 02    	mov    %es:0x2b4(%bp),%ebx
    19e2:	e8 e9 fe             	call   0x18ce
    19e5:	66 5b                	pop    %ebx
    19e7:	66 51                	push   %ecx
    19e9:	66 26 8b 8e b8 02    	mov    %es:0x2b8(%bp),%ecx
    19ef:	e8 f7 fe             	call   0x18e9
    19f2:	66 59                	pop    %ecx
    19f4:	66 52                	push   %edx
    19f6:	66 26 8b 96 bc 02    	mov    %es:0x2bc(%bp),%edx
    19fc:	e8 05 ff             	call   0x1904
    19ff:	66 5a                	pop    %edx
    1a01:	66 57                	push   %edi
    1a03:	66 26 8b be c0 02    	mov    %es:0x2c0(%bp),%edi
    1a09:	e8 13 ff             	call   0x191f
    1a0c:	66 5f                	pop    %edi
    1a0e:	66 56                	push   %esi
    1a10:	66 26 8b b6 c4 02    	mov    %es:0x2c4(%bp),%esi
    1a16:	e8 21 ff             	call   0x193a
    1a19:	66 5e                	pop    %esi
    1a1b:	1e                   	push   %ds
    1a1c:	26 8e 9e c8 02       	mov    %es:0x2c8(%bp),%ds
    1a21:	e8 3a fe             	call   0x185e
    1a24:	1f                   	pop    %ds
    1a25:	06                   	push   %es
    1a26:	26 8e 86 ca 02       	mov    %es:0x2ca(%bp),%es
    1a2b:	e8 1b fe             	call   0x1849
    1a2e:	07                   	pop    %es
    1a2f:	0f a0                	push   %fs
    1a31:	26 8e a6 ce 02       	mov    %es:0x2ce(%bp),%fs
    1a36:	e8 64 fe             	call   0x189d
    1a39:	0f a1                	pop    %fs
    1a3b:	0f a8                	push   %gs
    1a3d:	26 8e ae cc 02       	mov    %es:0x2cc(%bp),%gs
    1a42:	e8 43 fe             	call   0x1888
    1a45:	0f a9                	pop    %gs
    1a47:	e8 26 ff             	call   0x1970
    1a4a:	e8 26 fe             	call   0x1873
    1a4d:	9d                   	popf   
    1a4e:	c3                   	ret    
    1a4f:	0d 0a 00             	or     $0xa,%ax
    1a52:	0d 0a 07             	or     $0x70a,%ax
    1a55:	44                   	inc    %sp
    1a56:	41                   	inc    %cx
    1a57:	43                   	inc    %bx
    1a58:	39 36 30 3a          	cmp    %si,0x3a30
    1a5c:	20 73 79             	and    %dh,0x79(%bp,%di)
    1a5f:	73 74                	jae    0x1ad5
    1a61:	65 6d                	gs insw (%dx),%es:(%di)
    1a63:	20 42 49             	and    %al,0x49(%bp,%si)
    1a66:	4f                   	dec    %di
    1a67:	53                   	push   %bx
    1a68:	20 46 61             	and    %al,0x61(%bp)
    1a6b:	74 61                	je     0x1ace
    1a6d:	6c                   	insb   (%dx),%es:(%di)
    1a6e:	20 45 72             	and    %al,0x72(%di)
    1a71:	72 6f                	jb     0x1ae2
    1a73:	72 20                	jb     0x1a95
    1a75:	2d 20 49             	sub    $0x4920,%ax
    1a78:	4e                   	dec    %si
    1a79:	54                   	push   %sp
    1a7a:	20 31                	and    %dh,(%bx,%di)
    1a7c:	35 48 20             	xor    $0x2048,%ax
    1a7f:	66 75 6e             	data32 jne 0x1af0
    1a82:	63 74 69             	arpl   %si,0x69(%si)
    1a85:	6f                   	outsw  %ds:(%si),(%dx)
    1a86:	6e                   	outsb  %ds:(%si),(%dx)
    1a87:	20 38                	and    %bh,(%bx,%si)
    1a89:	37                   	aaa    
    1a8a:	48                   	dec    %ax
    1a8b:	20 28                	and    %ch,(%bx,%si)
    1a8d:	43                   	inc    %bx
    1a8e:	6f                   	outsw  %ds:(%si),(%dx)
    1a8f:	70 79                	jo     0x1b0a
    1a91:	20 65 78             	and    %ah,0x78(%di)
    1a94:	74 65                	je     0x1afb
    1a96:	6e                   	outsb  %ds:(%si),(%dx)
    1a97:	64 65 64 20 6d 65    	fs gs and %ch,%fs:0x65(%di)
    1a9d:	6d                   	insw   (%dx),%es:(%di)
    1a9e:	6f                   	outsw  %ds:(%si),(%dx)
    1a9f:	72 79                	jb     0x1b1a
    1aa1:	29 20                	sub    %sp,(%bx,%si)
    1aa3:	66 61                	popal  
    1aa5:	69 6c 65 64 2e       	imul   $0x2e64,0x65(%si),%bp
    1aaa:	00 0d                	add    %cl,(%di)
    1aac:	0a 07                	or     (%bx),%al
    1aae:	44                   	inc    %sp
    1aaf:	41                   	inc    %cx
    1ab0:	43                   	inc    %bx
    1ab1:	39 36 30 3a          	cmp    %si,0x3a30
    1ab5:	20 73 79             	and    %dh,0x79(%bp,%di)
    1ab8:	73 74                	jae    0x1b2e
    1aba:	65 6d                	gs insw (%dx),%es:(%di)
    1abc:	20 42 49             	and    %al,0x49(%bp,%si)
    1abf:	4f                   	dec    %di
    1ac0:	53                   	push   %bx
    1ac1:	20 66 61             	and    %ah,0x61(%bp)
    1ac4:	74 61                	je     0x1b27
    1ac6:	72 20                	jb     0x1ae8
    1ac8:	45                   	inc    %bp
    1ac9:	72 72                	jb     0x1b3d
    1acb:	6f                   	outsw  %ds:(%si),(%dx)
    1acc:	72 20                	jb     0x1aee
    1ace:	2d 20 49             	sub    $0x4920,%ax
    1ad1:	4e                   	dec    %si
    1ad2:	54                   	push   %sp
    1ad3:	20 34                	and    %dh,(%si)
    1ad5:	42                   	inc    %dx
    1ad6:	48                   	dec    %ax
    1ad7:	20 66 75             	and    %ah,0x75(%bp)
    1ada:	6e                   	outsb  %ds:(%si),(%dx)
    1adb:	63 74 69             	arpl   %si,0x69(%si)
    1ade:	6f                   	outsw  %ds:(%si),(%dx)
    1adf:	6e                   	outsb  %ds:(%si),(%dx)
    1ae0:	20 38                	and    %bh,(%bx,%si)
    1ae2:	31 30                	xor    %si,(%bx,%si)
    1ae4:	35 48 20             	xor    $0x2048,%ax
    1ae7:	28 53 63             	sub    %dl,0x63(%bp,%di)
    1aea:	61                   	popa   
    1aeb:	74 74                	je     0x1b61
    1aed:	65 72 2f             	gs jb  0x1b1f
    1af0:	47                   	inc    %di
    1af1:	61                   	popa   
    1af2:	74 68                	je     0x1b5c
    1af4:	65 72 20             	gs jb  0x1b17
    1af7:	6c                   	insb   (%dx),%es:(%di)
    1af8:	6f                   	outsw  %ds:(%si),(%dx)
    1af9:	63 6b 20             	arpl   %bp,0x20(%bp,%di)
    1afc:	72 65                	jb     0x1b63
    1afe:	67 69 6f 6e 20 66    	imul   $0x6620,0x6e(%edi),%bp
    1b04:	61                   	popa   
    1b05:	69 6c 65 64 2e       	imul   $0x2e64,0x65(%si),%bp
    1b0a:	00 0d                	add    %cl,(%di)
    1b0c:	0a 53 59             	or     0x59(%bp,%di),%dl
    1b0f:	53                   	push   %bx
    1b10:	54                   	push   %sp
    1b11:	45                   	inc    %bp
    1b12:	4d                   	dec    %bp
    1b13:	20 49 53             	and    %cl,0x53(%bx,%di)
    1b16:	20 4f 4e             	and    %cl,0x4e(%bx)
    1b19:	20 48 4f             	and    %cl,0x4f(%bx,%si)
    1b1c:	4c                   	dec    %sp
    1b1d:	44                   	inc    %sp
    1b1e:	20 54 49             	and    %dl,0x49(%si)
    1b21:	4c                   	dec    %sp
    1b22:	4c                   	dec    %sp
    1b23:	20 59 4f             	and    %bl,0x4f(%bx,%di)
    1b26:	55                   	push   %bp
    1b27:	20 50 52             	and    %dl,0x52(%bx,%si)
    1b2a:	45                   	inc    %bp
    1b2b:	53                   	push   %bx
    1b2c:	53                   	push   %bx
    1b2d:	20 41 20             	and    %al,0x20(%bx,%di)
    1b30:	4b                   	dec    %bx
    1b31:	45                   	inc    %bp
    1b32:	59                   	pop    %cx
    1b33:	00 0d                	add    %cl,(%di)
    1b35:	0a 43 68             	or     0x68(%bp,%di),%al
    1b38:	65 63 6b 69          	arpl   %bp,%gs:0x69(%bp,%di)
    1b3c:	6e                   	outsb  %ds:(%si),(%dx)
    1b3d:	67 20 52 41          	and    %dl,0x41(%edx)
    1b41:	49                   	dec    %cx
    1b42:	44                   	inc    %sp
    1b43:	20 43 6f             	and    %al,0x6f(%bp,%di)
    1b46:	6e                   	outsb  %ds:(%si),(%dx)
    1b47:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    1b4e:	69 
    1b4f:	6f                   	outsw  %ds:(%si),(%dx)
    1b50:	6e                   	outsb  %ds:(%si),(%dx)
    1b51:	20 73 6f             	and    %dh,0x6f(%bp,%di)
    1b54:	66 74 77             	data32 je 0x1bce
    1b57:	61                   	popa   
    1b58:	72 65                	jb     0x1bbf
    1b5a:	20 2e 2e 2e          	and    %ch,0x2e2e
    1b5e:	20 00                	and    %al,(%bx,%si)
    1b60:	0d 0a 4c             	or     $0x4c0a,%ax
    1b63:	6f                   	outsw  %ds:(%si),(%dx)
    1b64:	61                   	popa   
    1b65:	64 69 6e 67 20 52    	imul   $0x5220,%fs:0x67(%bp),%bp
    1b6b:	41                   	inc    %cx
    1b6c:	49                   	dec    %cx
    1b6d:	44                   	inc    %sp
    1b6e:	20 43 6f             	and    %al,0x6f(%bp,%di)
    1b71:	6e                   	outsb  %ds:(%si),(%dx)
    1b72:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    1b79:	69 
    1b7a:	6f                   	outsw  %ds:(%si),(%dx)
    1b7b:	6e                   	outsb  %ds:(%si),(%dx)
    1b7c:	20 73 6f             	and    %dh,0x6f(%bp,%di)
    1b7f:	66 74 77             	data32 je 0x1bf9
    1b82:	61                   	popa   
    1b83:	72 65                	jb     0x1bea
    1b85:	20 2e 2e 2e          	and    %ch,0x2e2e
    1b89:	20 00                	and    %al,(%bx,%si)
    1b8b:	0d 0a 53             	or     $0x530a,%ax
    1b8e:	74 61                	je     0x1bf1
    1b90:	72 74                	jb     0x1c06
    1b92:	69 6e 67 20 52       	imul   $0x5220,0x67(%bp),%bp
    1b97:	41                   	inc    %cx
    1b98:	49                   	dec    %cx
    1b99:	44                   	inc    %sp
    1b9a:	20 43 6f             	and    %al,0x6f(%bp,%di)
    1b9d:	6e                   	outsb  %ds:(%si),(%dx)
    1b9e:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    1ba5:	69 
    1ba6:	6f                   	outsw  %ds:(%si),(%dx)
    1ba7:	6e                   	outsb  %ds:(%si),(%dx)
    1ba8:	20 73 6f             	and    %dh,0x6f(%bp,%di)
    1bab:	66 74 77             	data32 je 0x1c25
    1bae:	61                   	popa   
    1baf:	72 65                	jb     0x1c16
    1bb1:	20 2e 2e 2e          	and    %ch,0x2e2e
    1bb5:	20 00                	and    %al,(%bx,%si)
    1bb7:	0d 0a 52             	or     $0x520a,%ax
    1bba:	41                   	inc    %cx
    1bbb:	49                   	dec    %cx
    1bbc:	44                   	inc    %sp
    1bbd:	20 43 6f             	and    %al,0x6f(%bp,%di)
    1bc0:	6e                   	outsb  %ds:(%si),(%dx)
    1bc1:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    1bc8:	69 
    1bc9:	6f                   	outsw  %ds:(%si),(%dx)
    1bca:	6e                   	outsb  %ds:(%si),(%dx)
    1bcb:	20 73 6f             	and    %dh,0x6f(%bp,%di)
    1bce:	66 74 77             	data32 je 0x1c48
    1bd1:	61                   	popa   
    1bd2:	72 65                	jb     0x1c39
    1bd4:	20 6e 6f             	and    %ch,0x6f(%bp)
    1bd7:	74 20                	je     0x1bf9
    1bd9:	66 6f                	outsl  %ds:(%si),(%dx)
    1bdb:	75 6e                	jne    0x1c4b
    1bdd:	64 00 00             	add    %al,%fs:(%bx,%si)
	...
    1be8:	00 00                	add    %al,(%bx,%si)
    1bea:	af                   	scas   %es:(%di),%ax
    1beb:	02 25                	add    (%di),%ah
    1bed:	02 12                	add    (%bp,%si),%dl
    1bef:	1b ff                	sbb    %di,%di
    1bf1:	6c                   	insb   (%dx),%es:(%di)
    1bf2:	f6 0f 08             	testb  $0x8,(%bx)
    1bf5:	90                   	nop
    1bf6:	20 7f 00             	and    %bh,0x0(%bx)
    1bf9:	00 00                	add    %al,(%bx,%si)
    1bfb:	00 00                	add    %al,(%bx,%si)
    1bfd:	00 00                	add    %al,(%bx,%si)
    1bff:	00 40 00             	add    %al,0x0(%bx,%si)
    1c02:	00 00                	add    %al,(%bx,%si)
    1c04:	00 10                	add    %dl,(%bx,%si)
    1c06:	8b c0                	mov    %ax,%ax
	...
    1c18:	00 00                	add    %al,(%bx,%si)
    1c1a:	ff                   	(bad)  
    1c1b:	ff f6                	push   %si
    1c1d:	04 03                	add    $0x3,%al
    1c1f:	05 4d 07             	add    $0x74d,%ax
    1c22:	45                   	inc    %bp
    1c23:	07                   	pop    %es
    1c24:	f2 04 7d             	repnz add $0x7d,%al
    1c27:	04 7d                	add    $0x7d,%al
    1c29:	04 7d                	add    $0x7d,%al
    1c2b:	04 49                	add    $0x49,%al
    1c2d:	05 f2 04             	add    $0x4f2,%ax
    1c30:	7d 04                	jge    0x1c36
    1c32:	7d 04                	jge    0x1c38
    1c34:	f2 04 f2             	repnz add $0xf2,%al
    1c37:	04 7d                	add    $0x7d,%al
    1c39:	04 7d                	add    $0x7d,%al
    1c3b:	04 f2                	add    $0xf2,%al
    1c3d:	04 f2                	add    $0xf2,%al
    1c3f:	04 7d                	add    $0x7d,%al
    1c41:	04 7d                	add    $0x7d,%al
    1c43:	04 f2                	add    $0xf2,%al
    1c45:	04 10                	add    $0x10,%al
    1c47:	05 f2 04             	add    $0x4f2,%ax
    1c4a:	7d 04                	jge    0x1c50
    1c4c:	7d 04                	jge    0x1c52
    1c4e:	7d 04                	jge    0x1c54
    1c50:	7d 04                	jge    0x1c56
    1c52:	7d 04                	jge    0x1c58
    1c54:	7d 04                	jge    0x1c5a
    1c56:	7d 04                	jge    0x1c5c
    1c58:	7d 04                	jge    0x1c5e
    1c5a:	7d 04                	jge    0x1c60
    1c5c:	7d 04                	jge    0x1c62
    1c5e:	7d 04                	jge    0x1c64
    1c60:	7d 04                	jge    0x1c66
    1c62:	7d 04                	jge    0x1c68
    1c64:	7d 04                	jge    0x1c6a
    1c66:	7d 04                	jge    0x1c6c
    1c68:	7d 04                	jge    0x1c6e
    1c6a:	7d 04                	jge    0x1c70
    1c6c:	7d 04                	jge    0x1c72
    1c6e:	7d 04                	jge    0x1c74
    1c70:	7d 04                	jge    0x1c76
    1c72:	7d 04                	jge    0x1c78
    1c74:	7d 04                	jge    0x1c7a
    1c76:	7d 04                	jge    0x1c7c
    1c78:	7d 04                	jge    0x1c7e
    1c7a:	7d 04                	jge    0x1c80
    1c7c:	7d 04                	jge    0x1c82
    1c7e:	7d 04                	jge    0x1c84
    1c80:	7d 04                	jge    0x1c86
    1c82:	7d 04                	jge    0x1c88
    1c84:	7d 04                	jge    0x1c8a
    1c86:	7d 04                	jge    0x1c8c
    1c88:	7d 04                	jge    0x1c8e
    1c8a:	7d 04                	jge    0x1c90
    1c8c:	7d 04                	jge    0x1c92
    1c8e:	7d 04                	jge    0x1c94
    1c90:	7d 04                	jge    0x1c96
    1c92:	7d 04                	jge    0x1c98
    1c94:	7d 04                	jge    0x1c9a
    1c96:	7d 04                	jge    0x1c9c
    1c98:	7d 04                	jge    0x1c9e
    1c9a:	7d 04                	jge    0x1ca0
    1c9c:	7d 04                	jge    0x1ca2
    1c9e:	81 0a c6 0a          	orw    $0xac6,(%bp,%si)
    1ca2:	a6                   	cmpsb  %es:(%di),%ds:(%si)
    1ca3:	0a f2                	or     %dl,%dh
    1ca5:	04 ee                	add    $0xee,%al
    1ca7:	04 ee                	add    $0xee,%al
    1ca9:	04 f2                	add    $0xf2,%al
    1cab:	04 12                	add    $0x12,%al
    1cad:	0a c0                	or     %al,%al
    1caf:	09 ee                	or     %bp,%si
    1cb1:	04 ca                	add    $0xca,%al
    1cb3:	09 ee                	or     %bp,%si
    1cb5:	04 ee                	add    $0xee,%al
    1cb7:	04 33                	add    $0x33,%al
    1cb9:	c0 cb 2e             	ror    $0x2e,%bl
    1cbc:	8b c0                	mov    %ax,%ax
    1cbe:	8b c0                	mov    %ax,%ax
	...
    20c0:	ff                   	(bad)  
    20c1:	ff                   	(bad)  
    20c2:	ff                   	(bad)  
    20c3:	ff                   	(bad)  
    20c4:	ff                   	(bad)  
    20c5:	ff                   	(bad)  
    20c6:	ff                   	(bad)  
    20c7:	ff                   	(bad)  
    20c8:	ff                   	(bad)  
    20c9:	ff                   	(bad)  
    20ca:	ff                   	(bad)  
    20cb:	ff                   	(bad)  
    20cc:	ff                   	(bad)  
    20cd:	ff                   	(bad)  
    20ce:	ff                   	(bad)  
    20cf:	ff                   	(bad)  
    20d0:	ff                   	(bad)  
    20d1:	ff                   	(bad)  
    20d2:	ff                   	(bad)  
    20d3:	ff                   	(bad)  
    20d4:	ff                   	(bad)  
    20d5:	ff                   	(bad)  
    20d6:	ff                   	(bad)  
    20d7:	ff                   	(bad)  
    20d8:	ff                   	(bad)  
    20d9:	ff                   	(bad)  
    20da:	ff                   	(bad)  
    20db:	ff                   	(bad)  
    20dc:	ff                   	(bad)  
    20dd:	ff                   	(bad)  
    20de:	ff                   	(bad)  
    20df:	ff                   	(bad)  
    20e0:	ff                   	(bad)  
    20e1:	ff                   	(bad)  
    20e2:	ff                   	(bad)  
    20e3:	ff                   	(bad)  
    20e4:	ff                   	(bad)  
    20e5:	ff                   	(bad)  
    20e6:	ff                   	(bad)  
    20e7:	ff                   	(bad)  
    20e8:	ff                   	(bad)  
    20e9:	ff                   	(bad)  
    20ea:	ff                   	(bad)  
    20eb:	ff                   	(bad)  
    20ec:	ff                   	(bad)  
    20ed:	ff                   	(bad)  
    20ee:	ff                   	(bad)  
    20ef:	ff                   	(bad)  
    20f0:	ff                   	(bad)  
    20f1:	ff                   	(bad)  
    20f2:	ff                   	(bad)  
    20f3:	ff                   	(bad)  
    20f4:	ff                   	(bad)  
    20f5:	ff                   	(bad)  
    20f6:	ff                   	(bad)  
    20f7:	ff                   	(bad)  
    20f8:	ff                   	(bad)  
    20f9:	ff                   	(bad)  
    20fa:	ff                   	(bad)  
    20fb:	ff                   	(bad)  
    20fc:	ff                   	(bad)  
    20fd:	ff                   	(bad)  
    20fe:	ff                   	(bad)  
    20ff:	ff                   	(bad)  
    2100:	ff                   	(bad)  
    2101:	ff                   	(bad)  
    2102:	ff                   	(bad)  
    2103:	ff                   	(bad)  
    2104:	ff                   	(bad)  
    2105:	ff                   	(bad)  
    2106:	ff                   	(bad)  
    2107:	ff                   	(bad)  
    2108:	ff                   	(bad)  
    2109:	ff                   	(bad)  
    210a:	ff                   	(bad)  
    210b:	ff                   	(bad)  
    210c:	ff                   	(bad)  
    210d:	ff                   	(bad)  
    210e:	ff                   	(bad)  
    210f:	ff                   	(bad)  
    2110:	ff                   	(bad)  
    2111:	ff                   	(bad)  
    2112:	ff                   	(bad)  
    2113:	ff                   	(bad)  
    2114:	ff                   	(bad)  
    2115:	ff                   	(bad)  
    2116:	ff                   	(bad)  
    2117:	ff                   	(bad)  
    2118:	ff                   	(bad)  
    2119:	ff                   	(bad)  
    211a:	ff                   	(bad)  
    211b:	ff                   	(bad)  
    211c:	ff                   	(bad)  
    211d:	ff                   	(bad)  
    211e:	ff                   	(bad)  
    211f:	ff                   	(bad)  
    2120:	ff                   	(bad)  
    2121:	ff                   	(bad)  
    2122:	ff                   	(bad)  
    2123:	ff                   	(bad)  
    2124:	ff                   	(bad)  
    2125:	ff                   	(bad)  
    2126:	ff                   	(bad)  
    2127:	ff                   	(bad)  
    2128:	ff                   	(bad)  
    2129:	ff                   	(bad)  
    212a:	ff                   	(bad)  
    212b:	ff                   	(bad)  
    212c:	ff                   	(bad)  
    212d:	ff                   	(bad)  
    212e:	ff                   	(bad)  
    212f:	ff                   	(bad)  
    2130:	ff                   	(bad)  
    2131:	ff                   	(bad)  
    2132:	ff                   	(bad)  
    2133:	ff                   	(bad)  
    2134:	ff                   	(bad)  
    2135:	ff                   	(bad)  
    2136:	ff                   	(bad)  
    2137:	ff                   	(bad)  
    2138:	ff                   	(bad)  
    2139:	ff                   	(bad)  
    213a:	ff                   	(bad)  
    213b:	ff                   	(bad)  
    213c:	ff                   	(bad)  
    213d:	ff                   	(bad)  
    213e:	ff                   	(bad)  
    213f:	ff                   	(bad)  
    2140:	ff                   	(bad)  
    2141:	ff                   	(bad)  
    2142:	ff                   	(bad)  
    2143:	ff                   	(bad)  
    2144:	ff                   	(bad)  
    2145:	ff                   	(bad)  
    2146:	ff                   	(bad)  
    2147:	ff                   	(bad)  
    2148:	ff                   	(bad)  
    2149:	ff                   	(bad)  
    214a:	ff                   	(bad)  
    214b:	ff                   	(bad)  
    214c:	ff                   	(bad)  
    214d:	ff                   	(bad)  
    214e:	ff                   	(bad)  
    214f:	ff                   	(bad)  
    2150:	ff                   	(bad)  
    2151:	ff                   	(bad)  
    2152:	ff                   	(bad)  
    2153:	ff                   	(bad)  
    2154:	ff                   	(bad)  
    2155:	ff                   	(bad)  
    2156:	ff                   	(bad)  
    2157:	ff                   	(bad)  
    2158:	ff                   	(bad)  
    2159:	ff                   	(bad)  
    215a:	ff                   	(bad)  
    215b:	ff                   	(bad)  
    215c:	ff                   	(bad)  
    215d:	ff                   	(bad)  
    215e:	ff                   	(bad)  
    215f:	ff                   	(bad)  
    2160:	ff                   	(bad)  
    2161:	ff                   	(bad)  
    2162:	ff                   	(bad)  
    2163:	ff                   	(bad)  
    2164:	ff                   	(bad)  
    2165:	ff                   	(bad)  
    2166:	ff                   	(bad)  
    2167:	ff                   	(bad)  
    2168:	ff                   	(bad)  
    2169:	ff                   	(bad)  
    216a:	ff                   	(bad)  
    216b:	ff                   	(bad)  
    216c:	ff                   	(bad)  
    216d:	ff                   	(bad)  
    216e:	ff                   	(bad)  
    216f:	ff                   	(bad)  
    2170:	ff                   	(bad)  
    2171:	ff                   	(bad)  
    2172:	ff                   	(bad)  
    2173:	ff                   	(bad)  
    2174:	ff                   	(bad)  
    2175:	ff                   	(bad)  
    2176:	ff                   	(bad)  
    2177:	ff                   	(bad)  
    2178:	ff                   	(bad)  
    2179:	ff                   	(bad)  
    217a:	ff                   	(bad)  
    217b:	ff                   	(bad)  
    217c:	ff                   	(bad)  
    217d:	ff                   	(bad)  
    217e:	ff                   	(bad)  
    217f:	ff                   	(bad)  
    2180:	ff                   	(bad)  
    2181:	ff                   	(bad)  
    2182:	ff                   	(bad)  
    2183:	ff                   	(bad)  
    2184:	ff                   	(bad)  
    2185:	ff                   	(bad)  
    2186:	ff                   	(bad)  
    2187:	ff                   	(bad)  
    2188:	ff                   	(bad)  
    2189:	ff                   	(bad)  
    218a:	ff                   	(bad)  
    218b:	ff                   	(bad)  
    218c:	ff                   	(bad)  
    218d:	ff                   	(bad)  
    218e:	ff                   	(bad)  
    218f:	ff                   	(bad)  
    2190:	ff                   	(bad)  
    2191:	ff                   	(bad)  
    2192:	ff                   	(bad)  
    2193:	ff                   	(bad)  
    2194:	ff                   	(bad)  
    2195:	ff                   	(bad)  
    2196:	ff                   	(bad)  
    2197:	ff                   	(bad)  
    2198:	ff                   	(bad)  
    2199:	ff                   	(bad)  
    219a:	ff                   	(bad)  
    219b:	ff                   	(bad)  
    219c:	ff                   	(bad)  
    219d:	ff                   	(bad)  
    219e:	ff                   	(bad)  
    219f:	ff                   	(bad)  
    21a0:	ff                   	(bad)  
    21a1:	ff                   	(bad)  
    21a2:	ff                   	(bad)  
    21a3:	ff                   	(bad)  
    21a4:	ff                   	(bad)  
    21a5:	ff                   	(bad)  
    21a6:	ff                   	(bad)  
    21a7:	ff                   	(bad)  
    21a8:	ff                   	(bad)  
    21a9:	ff                   	(bad)  
    21aa:	ff                   	(bad)  
    21ab:	ff                   	(bad)  
    21ac:	ff                   	(bad)  
    21ad:	ff                   	(bad)  
    21ae:	ff                   	(bad)  
    21af:	ff                   	(bad)  
    21b0:	ff                   	(bad)  
    21b1:	ff                   	(bad)  
    21b2:	ff                   	(bad)  
    21b3:	ff                   	(bad)  
    21b4:	ff                   	(bad)  
    21b5:	ff                   	(bad)  
    21b6:	ff                   	(bad)  
    21b7:	ff                   	(bad)  
    21b8:	ff                   	(bad)  
    21b9:	ff                   	(bad)  
    21ba:	ff                   	(bad)  
    21bb:	ff                   	(bad)  
    21bc:	ff                   	(bad)  
    21bd:	ff                   	(bad)  
    21be:	ff                   	(bad)  
    21bf:	ff                   	(bad)  
    21c0:	ff                   	(bad)  
    21c1:	ff                   	(bad)  
    21c2:	ff                   	(bad)  
    21c3:	ff                   	(bad)  
    21c4:	ff                   	(bad)  
    21c5:	ff                   	(bad)  
    21c6:	ff                   	(bad)  
    21c7:	ff                   	(bad)  
    21c8:	ff                   	(bad)  
    21c9:	ff                   	(bad)  
    21ca:	ff                   	(bad)  
    21cb:	ff                   	(bad)  
    21cc:	ff                   	(bad)  
    21cd:	ff                   	(bad)  
    21ce:	ff                   	(bad)  
    21cf:	ff                   	(bad)  
    21d0:	ff                   	(bad)  
    21d1:	ff                   	(bad)  
    21d2:	ff                   	(bad)  
    21d3:	ff                   	(bad)  
    21d4:	ff                   	(bad)  
    21d5:	ff                   	(bad)  
    21d6:	ff                   	(bad)  
    21d7:	ff                   	(bad)  
    21d8:	ff                   	(bad)  
    21d9:	ff                   	(bad)  
    21da:	ff                   	(bad)  
    21db:	ff                   	(bad)  
    21dc:	ff                   	(bad)  
    21dd:	ff                   	(bad)  
    21de:	ff                   	(bad)  
    21df:	ff                   	(bad)  
    21e0:	ff                   	(bad)  
    21e1:	ff                   	(bad)  
    21e2:	ff                   	(bad)  
    21e3:	ff                   	(bad)  
    21e4:	ff                   	(bad)  
    21e5:	ff                   	(bad)  
    21e6:	ff                   	(bad)  
    21e7:	ff                   	(bad)  
    21e8:	ff                   	(bad)  
    21e9:	ff                   	(bad)  
    21ea:	ff                   	(bad)  
    21eb:	ff                   	(bad)  
    21ec:	ff                   	(bad)  
    21ed:	ff                   	(bad)  
    21ee:	ff                   	(bad)  
    21ef:	ff                   	(bad)  
    21f0:	ff                   	(bad)  
    21f1:	ff                   	(bad)  
    21f2:	ff                   	(bad)  
    21f3:	ff                   	(bad)  
    21f4:	ff                   	(bad)  
    21f5:	ff                   	(bad)  
    21f6:	ff                   	(bad)  
    21f7:	ff                   	(bad)  
    21f8:	ff                   	(bad)  
    21f9:	ff                   	(bad)  
    21fa:	ff                   	(bad)  
    21fb:	ff                   	(bad)  
    21fc:	ff                   	(bad)  
    21fd:	ff                   	(bad)  
    21fe:	ff                   	(bad)  
    21ff:	ff                   	(bad)  
    2200:	ff                   	(bad)  
    2201:	ff                   	(bad)  
    2202:	ff                   	(bad)  
    2203:	ff                   	(bad)  
    2204:	ff                   	(bad)  
    2205:	ff                   	(bad)  
    2206:	ff                   	(bad)  
    2207:	ff                   	(bad)  
    2208:	ff                   	(bad)  
    2209:	ff                   	(bad)  
    220a:	ff                   	(bad)  
    220b:	ff                   	(bad)  
    220c:	ff                   	(bad)  
    220d:	ff                   	(bad)  
    220e:	ff                   	(bad)  
    220f:	ff                   	(bad)  
    2210:	ff                   	(bad)  
    2211:	ff                   	(bad)  
    2212:	ff                   	(bad)  
    2213:	ff                   	(bad)  
    2214:	ff                   	(bad)  
    2215:	ff                   	(bad)  
    2216:	ff                   	(bad)  
    2217:	ff                   	(bad)  
    2218:	ff                   	(bad)  
    2219:	ff                   	(bad)  
    221a:	ff                   	(bad)  
    221b:	ff                   	(bad)  
    221c:	ff                   	(bad)  
    221d:	ff                   	(bad)  
    221e:	ff                   	(bad)  
    221f:	ff                   	(bad)  
    2220:	ff                   	(bad)  
    2221:	ff                   	(bad)  
    2222:	ff                   	(bad)  
    2223:	ff                   	(bad)  
    2224:	ff                   	(bad)  
    2225:	ff                   	(bad)  
    2226:	ff                   	(bad)  
    2227:	ff                   	(bad)  
    2228:	ff                   	(bad)  
    2229:	ff                   	(bad)  
    222a:	ff                   	(bad)  
    222b:	ff                   	(bad)  
    222c:	ff                   	(bad)  
    222d:	ff                   	(bad)  
    222e:	ff                   	(bad)  
    222f:	ff                   	(bad)  
    2230:	ff                   	(bad)  
    2231:	ff                   	(bad)  
    2232:	ff                   	(bad)  
    2233:	ff                   	(bad)  
    2234:	ff                   	(bad)  
    2235:	ff                   	(bad)  
    2236:	ff                   	(bad)  
    2237:	ff                   	(bad)  
    2238:	ff                   	(bad)  
    2239:	ff                   	(bad)  
    223a:	ff                   	(bad)  
    223b:	ff                   	(bad)  
    223c:	ff                   	(bad)  
    223d:	ff                   	(bad)  
    223e:	ff                   	(bad)  
    223f:	ff                   	(bad)  
    2240:	ff                   	(bad)  
    2241:	ff                   	(bad)  
    2242:	ff                   	(bad)  
    2243:	ff                   	(bad)  
    2244:	ff                   	(bad)  
    2245:	ff                   	(bad)  
    2246:	ff                   	(bad)  
    2247:	ff                   	(bad)  
    2248:	ff                   	(bad)  
    2249:	ff                   	(bad)  
    224a:	ff                   	(bad)  
    224b:	ff                   	(bad)  
    224c:	ff                   	(bad)  
    224d:	ff                   	(bad)  
    224e:	ff                   	(bad)  
    224f:	ff                   	(bad)  
    2250:	ff                   	(bad)  
    2251:	ff                   	(bad)  
    2252:	ff                   	(bad)  
    2253:	ff                   	(bad)  
    2254:	ff                   	(bad)  
    2255:	ff                   	(bad)  
    2256:	ff                   	(bad)  
    2257:	ff                   	(bad)  
    2258:	ff                   	(bad)  
    2259:	ff                   	(bad)  
    225a:	ff                   	(bad)  
    225b:	ff                   	(bad)  
    225c:	ff                   	(bad)  
    225d:	ff                   	(bad)  
    225e:	ff                   	(bad)  
    225f:	ff                   	(bad)  
    2260:	ff                   	(bad)  
    2261:	ff                   	(bad)  
    2262:	ff                   	(bad)  
    2263:	ff                   	(bad)  
    2264:	ff                   	(bad)  
    2265:	ff                   	(bad)  
    2266:	ff                   	(bad)  
    2267:	ff                   	(bad)  
    2268:	ff                   	(bad)  
    2269:	ff                   	(bad)  
    226a:	ff                   	(bad)  
    226b:	ff                   	(bad)  
    226c:	ff                   	(bad)  
    226d:	ff                   	(bad)  
    226e:	ff                   	(bad)  
    226f:	ff                   	(bad)  
    2270:	ff                   	(bad)  
    2271:	ff                   	(bad)  
    2272:	ff                   	(bad)  
    2273:	ff                   	(bad)  
    2274:	ff                   	(bad)  
    2275:	ff                   	(bad)  
    2276:	ff                   	(bad)  
    2277:	ff                   	(bad)  
    2278:	ff                   	(bad)  
    2279:	ff                   	(bad)  
    227a:	ff                   	(bad)  
    227b:	ff                   	(bad)  
    227c:	ff                   	(bad)  
    227d:	ff                   	(bad)  
    227e:	ff                   	(bad)  
    227f:	ff                   	(bad)  
    2280:	ff                   	(bad)  
    2281:	ff                   	(bad)  
    2282:	ff                   	(bad)  
    2283:	ff                   	(bad)  
    2284:	ff                   	(bad)  
    2285:	ff                   	(bad)  
    2286:	ff                   	(bad)  
    2287:	ff                   	(bad)  
    2288:	ff                   	(bad)  
    2289:	ff                   	(bad)  
    228a:	ff                   	(bad)  
    228b:	ff                   	(bad)  
    228c:	ff                   	(bad)  
    228d:	ff                   	(bad)  
    228e:	ff                   	(bad)  
    228f:	ff                   	(bad)  
    2290:	ff                   	(bad)  
    2291:	ff                   	(bad)  
    2292:	ff                   	(bad)  
    2293:	ff                   	(bad)  
    2294:	ff                   	(bad)  
    2295:	ff                   	(bad)  
    2296:	ff                   	(bad)  
    2297:	ff                   	(bad)  
    2298:	ff                   	(bad)  
    2299:	ff                   	(bad)  
    229a:	ff                   	(bad)  
    229b:	ff                   	(bad)  
    229c:	ff                   	(bad)  
    229d:	ff                   	(bad)  
    229e:	ff                   	(bad)  
    229f:	ff                   	(bad)  
    22a0:	ff                   	(bad)  
    22a1:	ff                   	(bad)  
    22a2:	ff                   	(bad)  
    22a3:	ff                   	(bad)  
    22a4:	ff                   	(bad)  
    22a5:	ff                   	(bad)  
    22a6:	ff                   	(bad)  
    22a7:	ff                   	(bad)  
    22a8:	ff                   	(bad)  
    22a9:	ff                   	(bad)  
    22aa:	ff                   	(bad)  
    22ab:	ff                   	(bad)  
    22ac:	ff                   	(bad)  
    22ad:	ff                   	(bad)  
    22ae:	ff                   	(bad)  
    22af:	ff                   	(bad)  
    22b0:	ff                   	(bad)  
    22b1:	ff                   	(bad)  
    22b2:	ff                   	(bad)  
    22b3:	ff                   	(bad)  
    22b4:	ff                   	(bad)  
    22b5:	ff                   	(bad)  
    22b6:	ff                   	(bad)  
    22b7:	ff                   	(bad)  
    22b8:	ff                   	(bad)  
    22b9:	ff                   	(bad)  
    22ba:	ff                   	(bad)  
    22bb:	ff                   	(bad)  
    22bc:	ff                   	(bad)  
    22bd:	ff                   	(bad)  
    22be:	ff                   	(bad)  
    22bf:	ff                   	(bad)  
    22c0:	ff                   	(bad)  
    22c1:	ff                   	(bad)  
    22c2:	ff                   	(bad)  
    22c3:	ff                   	(bad)  
    22c4:	ff                   	(bad)  
    22c5:	ff                   	(bad)  
    22c6:	ff                   	(bad)  
    22c7:	ff                   	(bad)  
    22c8:	ff                   	(bad)  
    22c9:	ff                   	(bad)  
    22ca:	ff                   	(bad)  
    22cb:	ff                   	(bad)  
    22cc:	ff                   	(bad)  
    22cd:	ff                   	(bad)  
    22ce:	ff                   	(bad)  
    22cf:	ff                   	(bad)  
    22d0:	ff                   	(bad)  
    22d1:	ff                   	(bad)  
    22d2:	ff                   	(bad)  
    22d3:	ff                   	(bad)  
    22d4:	ff                   	(bad)  
    22d5:	ff                   	(bad)  
    22d6:	ff                   	(bad)  
    22d7:	ff                   	(bad)  
    22d8:	ff                   	(bad)  
    22d9:	ff                   	(bad)  
    22da:	ff                   	(bad)  
    22db:	ff                   	(bad)  
    22dc:	ff                   	(bad)  
    22dd:	ff                   	(bad)  
    22de:	ff                   	(bad)  
    22df:	ff                   	(bad)  
    22e0:	ff                   	(bad)  
    22e1:	ff                   	(bad)  
    22e2:	ff                   	(bad)  
    22e3:	ff                   	(bad)  
    22e4:	ff                   	(bad)  
    22e5:	ff                   	(bad)  
    22e6:	ff                   	(bad)  
    22e7:	ff                   	(bad)  
    22e8:	ff                   	(bad)  
    22e9:	ff                   	(bad)  
    22ea:	ff                   	(bad)  
    22eb:	ff                   	(bad)  
    22ec:	ff                   	(bad)  
    22ed:	ff                   	(bad)  
    22ee:	ff                   	(bad)  
    22ef:	ff                   	(bad)  
    22f0:	ff                   	(bad)  
    22f1:	ff                   	(bad)  
    22f2:	ff                   	(bad)  
    22f3:	ff                   	(bad)  
    22f4:	ff                   	(bad)  
    22f5:	ff                   	(bad)  
    22f6:	ff                   	(bad)  
    22f7:	ff                   	(bad)  
    22f8:	ff                   	(bad)  
    22f9:	ff                   	(bad)  
    22fa:	ff                   	(bad)  
    22fb:	ff                   	(bad)  
    22fc:	ff                   	(bad)  
    22fd:	ff                   	(bad)  
    22fe:	ff                   	(bad)  
    22ff:	ff                   	(bad)  
    2300:	ff                   	(bad)  
    2301:	ff                   	(bad)  
    2302:	ff                   	(bad)  
    2303:	ff                   	(bad)  
    2304:	ff                   	(bad)  
    2305:	ff                   	(bad)  
    2306:	ff                   	(bad)  
    2307:	ff                   	(bad)  
    2308:	ff                   	(bad)  
    2309:	ff                   	(bad)  
    230a:	ff                   	(bad)  
    230b:	ff                   	(bad)  
    230c:	ff                   	(bad)  
    230d:	ff                   	(bad)  
    230e:	ff                   	(bad)  
    230f:	ff                   	(bad)  
    2310:	ff                   	(bad)  
    2311:	ff                   	(bad)  
    2312:	ff                   	(bad)  
    2313:	ff                   	(bad)  
    2314:	ff                   	(bad)  
    2315:	ff                   	(bad)  
    2316:	ff                   	(bad)  
    2317:	ff                   	(bad)  
    2318:	ff                   	(bad)  
    2319:	ff                   	(bad)  
    231a:	ff                   	(bad)  
    231b:	ff                   	(bad)  
    231c:	ff                   	(bad)  
    231d:	ff                   	(bad)  
    231e:	ff                   	(bad)  
    231f:	ff                   	(bad)  
    2320:	ff                   	(bad)  
    2321:	ff                   	(bad)  
    2322:	ff                   	(bad)  
    2323:	ff                   	(bad)  
    2324:	ff                   	(bad)  
    2325:	ff                   	(bad)  
    2326:	ff                   	(bad)  
    2327:	ff                   	(bad)  
    2328:	ff                   	(bad)  
    2329:	ff                   	(bad)  
    232a:	ff                   	(bad)  
    232b:	ff                   	(bad)  
    232c:	ff                   	(bad)  
    232d:	ff                   	(bad)  
    232e:	ff                   	(bad)  
    232f:	ff                   	(bad)  
    2330:	ff                   	(bad)  
    2331:	ff                   	(bad)  
    2332:	ff                   	(bad)  
    2333:	ff                   	(bad)  
    2334:	ff                   	(bad)  
    2335:	ff                   	(bad)  
    2336:	ff                   	(bad)  
    2337:	ff                   	(bad)  
    2338:	ff                   	(bad)  
    2339:	ff                   	(bad)  
    233a:	ff                   	(bad)  
    233b:	ff                   	(bad)  
    233c:	ff                   	(bad)  
    233d:	ff                   	(bad)  
    233e:	ff                   	(bad)  
    233f:	ff                   	(bad)  
    2340:	ff                   	(bad)  
    2341:	ff                   	(bad)  
    2342:	ff                   	(bad)  
    2343:	ff                   	(bad)  
    2344:	ff                   	(bad)  
    2345:	ff                   	(bad)  
    2346:	ff                   	(bad)  
    2347:	ff                   	(bad)  
    2348:	ff                   	(bad)  
    2349:	ff                   	(bad)  
    234a:	ff                   	(bad)  
    234b:	ff                   	(bad)  
    234c:	ff                   	(bad)  
    234d:	ff                   	(bad)  
    234e:	ff                   	(bad)  
    234f:	ff                   	(bad)  
    2350:	ff                   	(bad)  
    2351:	ff                   	(bad)  
    2352:	ff                   	(bad)  
    2353:	ff                   	(bad)  
    2354:	ff                   	(bad)  
    2355:	ff                   	(bad)  
    2356:	ff                   	(bad)  
    2357:	ff                   	(bad)  
    2358:	ff                   	(bad)  
    2359:	ff                   	(bad)  
    235a:	ff                   	(bad)  
    235b:	ff                   	(bad)  
    235c:	ff                   	(bad)  
    235d:	ff                   	(bad)  
    235e:	ff                   	(bad)  
    235f:	ff                   	(bad)  
    2360:	ff                   	(bad)  
    2361:	ff                   	(bad)  
    2362:	ff                   	(bad)  
    2363:	ff                   	(bad)  
    2364:	ff                   	(bad)  
    2365:	ff                   	(bad)  
    2366:	ff                   	(bad)  
    2367:	ff                   	(bad)  
    2368:	ff                   	(bad)  
    2369:	ff                   	(bad)  
    236a:	ff                   	(bad)  
    236b:	ff                   	(bad)  
    236c:	ff                   	(bad)  
    236d:	ff                   	(bad)  
    236e:	ff                   	(bad)  
    236f:	ff                   	(bad)  
    2370:	ff                   	(bad)  
    2371:	ff                   	(bad)  
    2372:	ff                   	(bad)  
    2373:	ff                   	(bad)  
    2374:	ff                   	(bad)  
    2375:	ff                   	(bad)  
    2376:	ff                   	(bad)  
    2377:	ff                   	(bad)  
    2378:	ff                   	(bad)  
    2379:	ff                   	(bad)  
    237a:	ff                   	(bad)  
    237b:	ff                   	(bad)  
    237c:	ff                   	(bad)  
    237d:	ff                   	(bad)  
    237e:	ff                   	(bad)  
    237f:	ff                   	(bad)  
    2380:	ff                   	(bad)  
    2381:	ff                   	(bad)  
    2382:	ff                   	(bad)  
    2383:	ff                   	(bad)  
    2384:	ff                   	(bad)  
    2385:	ff                   	(bad)  
    2386:	ff                   	(bad)  
    2387:	ff                   	(bad)  
    2388:	ff                   	(bad)  
    2389:	ff                   	(bad)  
    238a:	ff                   	(bad)  
    238b:	ff                   	(bad)  
    238c:	ff                   	(bad)  
    238d:	ff                   	(bad)  
    238e:	ff                   	(bad)  
    238f:	ff                   	(bad)  
    2390:	ff                   	(bad)  
    2391:	ff                   	(bad)  
    2392:	ff                   	(bad)  
    2393:	ff                   	(bad)  
    2394:	ff                   	(bad)  
    2395:	ff                   	(bad)  
    2396:	ff                   	(bad)  
    2397:	ff                   	(bad)  
    2398:	ff                   	(bad)  
    2399:	ff                   	(bad)  
    239a:	ff                   	(bad)  
    239b:	ff                   	(bad)  
    239c:	ff                   	(bad)  
    239d:	ff                   	(bad)  
    239e:	ff                   	(bad)  
    239f:	ff                   	(bad)  
    23a0:	ff                   	(bad)  
    23a1:	ff                   	(bad)  
    23a2:	ff                   	(bad)  
    23a3:	ff                   	(bad)  
    23a4:	ff                   	(bad)  
    23a5:	ff                   	(bad)  
    23a6:	ff                   	(bad)  
    23a7:	ff                   	(bad)  
    23a8:	ff                   	(bad)  
    23a9:	ff                   	(bad)  
    23aa:	ff                   	(bad)  
    23ab:	ff                   	(bad)  
    23ac:	ff                   	(bad)  
    23ad:	ff                   	(bad)  
    23ae:	ff                   	(bad)  
    23af:	ff                   	(bad)  
    23b0:	ff                   	(bad)  
    23b1:	ff                   	(bad)  
    23b2:	ff                   	(bad)  
    23b3:	ff                   	(bad)  
    23b4:	ff                   	(bad)  
    23b5:	ff                   	(bad)  
    23b6:	ff                   	(bad)  
    23b7:	ff                   	(bad)  
    23b8:	ff                   	(bad)  
    23b9:	ff                   	(bad)  
    23ba:	ff                   	(bad)  
    23bb:	ff                   	(bad)  
    23bc:	ff                   	(bad)  
    23bd:	ff                   	(bad)  
    23be:	ff                   	(bad)  
    23bf:	ff                   	(bad)  
    23c0:	ff                   	(bad)  
    23c1:	ff                   	(bad)  
    23c2:	ff                   	(bad)  
    23c3:	ff                   	(bad)  
    23c4:	ff                   	(bad)  
    23c5:	ff                   	(bad)  
    23c6:	ff                   	(bad)  
    23c7:	ff                   	(bad)  
    23c8:	ff                   	(bad)  
    23c9:	ff                   	(bad)  
    23ca:	ff                   	(bad)  
    23cb:	ff                   	(bad)  
    23cc:	ff                   	(bad)  
    23cd:	ff                   	(bad)  
    23ce:	ff                   	(bad)  
    23cf:	ff                   	(bad)  
    23d0:	ff                   	(bad)  
    23d1:	ff                   	(bad)  
    23d2:	ff                   	(bad)  
    23d3:	ff                   	(bad)  
    23d4:	ff                   	(bad)  
    23d5:	ff                   	(bad)  
    23d6:	ff                   	(bad)  
    23d7:	ff                   	(bad)  
    23d8:	ff                   	(bad)  
    23d9:	ff                   	(bad)  
    23da:	ff                   	(bad)  
    23db:	ff                   	(bad)  
    23dc:	ff                   	(bad)  
    23dd:	ff                   	(bad)  
    23de:	ff                   	(bad)  
    23df:	ff                   	(bad)  
    23e0:	ff                   	(bad)  
    23e1:	ff                   	(bad)  
    23e2:	ff                   	(bad)  
    23e3:	ff                   	(bad)  
    23e4:	ff                   	(bad)  
    23e5:	ff                   	(bad)  
    23e6:	ff                   	(bad)  
    23e7:	ff                   	(bad)  
    23e8:	ff                   	(bad)  
    23e9:	ff                   	(bad)  
    23ea:	ff                   	(bad)  
    23eb:	ff                   	(bad)  
    23ec:	ff                   	(bad)  
    23ed:	ff                   	(bad)  
    23ee:	ff                   	(bad)  
    23ef:	ff                   	(bad)  
    23f0:	ff                   	(bad)  
    23f1:	ff                   	(bad)  
    23f2:	ff                   	(bad)  
    23f3:	ff                   	(bad)  
    23f4:	ff                   	(bad)  
    23f5:	ff                   	(bad)  
    23f6:	ff                   	(bad)  
    23f7:	ff                   	(bad)  
    23f8:	ff                   	(bad)  
    23f9:	ff                   	(bad)  
    23fa:	ff                   	(bad)  
    23fb:	ff                   	(bad)  
    23fc:	ff                   	(bad)  
    23fd:	ff                   	(bad)  
    23fe:	ff                   	(bad)  
    23ff:	ff                   	(bad)  
    2400:	ff                   	(bad)  
    2401:	ff                   	(bad)  
    2402:	ff                   	(bad)  
    2403:	ff                   	(bad)  
    2404:	ff                   	(bad)  
    2405:	ff                   	(bad)  
    2406:	ff                   	(bad)  
    2407:	ff                   	(bad)  
    2408:	ff                   	(bad)  
    2409:	ff                   	(bad)  
    240a:	ff                   	(bad)  
    240b:	ff                   	(bad)  
    240c:	ff                   	(bad)  
    240d:	ff                   	(bad)  
    240e:	ff                   	(bad)  
    240f:	ff                   	(bad)  
    2410:	ff                   	(bad)  
    2411:	ff                   	(bad)  
    2412:	ff                   	(bad)  
    2413:	ff                   	(bad)  
    2414:	ff                   	(bad)  
    2415:	ff                   	(bad)  
    2416:	ff                   	(bad)  
    2417:	ff                   	(bad)  
    2418:	ff                   	(bad)  
    2419:	ff                   	(bad)  
    241a:	ff                   	(bad)  
    241b:	ff                   	(bad)  
    241c:	ff                   	(bad)  
    241d:	ff                   	(bad)  
    241e:	ff                   	(bad)  
    241f:	ff                   	(bad)  
    2420:	ff                   	(bad)  
    2421:	ff                   	(bad)  
    2422:	ff                   	(bad)  
    2423:	ff                   	(bad)  
    2424:	ff                   	(bad)  
    2425:	ff                   	(bad)  
    2426:	ff                   	(bad)  
    2427:	ff                   	(bad)  
    2428:	ff                   	(bad)  
    2429:	ff                   	(bad)  
    242a:	ff                   	(bad)  
    242b:	ff                   	(bad)  
    242c:	ff                   	(bad)  
    242d:	ff                   	(bad)  
    242e:	ff                   	(bad)  
    242f:	ff                   	(bad)  
    2430:	ff                   	(bad)  
    2431:	ff                   	(bad)  
    2432:	ff                   	(bad)  
    2433:	ff                   	(bad)  
    2434:	ff                   	(bad)  
    2435:	ff                   	(bad)  
    2436:	ff                   	(bad)  
    2437:	ff                   	(bad)  
    2438:	ff                   	(bad)  
    2439:	ff                   	(bad)  
    243a:	ff                   	(bad)  
    243b:	ff                   	(bad)  
    243c:	ff                   	(bad)  
    243d:	ff                   	(bad)  
    243e:	ff                   	(bad)  
    243f:	ff                   	(bad)  
    2440:	ff                   	(bad)  
    2441:	ff                   	(bad)  
    2442:	ff                   	(bad)  
    2443:	ff                   	(bad)  
    2444:	ff                   	(bad)  
    2445:	ff                   	(bad)  
    2446:	ff                   	(bad)  
    2447:	ff                   	(bad)  
    2448:	ff                   	(bad)  
    2449:	ff                   	(bad)  
    244a:	ff                   	(bad)  
    244b:	ff                   	(bad)  
    244c:	ff                   	(bad)  
    244d:	ff                   	(bad)  
    244e:	ff                   	(bad)  
    244f:	ff                   	(bad)  
    2450:	ff                   	(bad)  
    2451:	ff                   	(bad)  
    2452:	ff                   	(bad)  
    2453:	ff                   	(bad)  
    2454:	ff                   	(bad)  
    2455:	ff                   	(bad)  
    2456:	ff                   	(bad)  
    2457:	ff                   	(bad)  
    2458:	ff                   	(bad)  
    2459:	ff                   	(bad)  
    245a:	ff                   	(bad)  
    245b:	ff                   	(bad)  
    245c:	ff                   	(bad)  
    245d:	ff                   	(bad)  
    245e:	ff                   	(bad)  
    245f:	ff                   	(bad)  
    2460:	ff                   	(bad)  
    2461:	ff                   	(bad)  
    2462:	ff                   	(bad)  
    2463:	ff                   	(bad)  
    2464:	ff                   	(bad)  
    2465:	ff                   	(bad)  
    2466:	ff                   	(bad)  
    2467:	ff                   	(bad)  
    2468:	ff                   	(bad)  
    2469:	ff                   	(bad)  
    246a:	ff                   	(bad)  
    246b:	ff                   	(bad)  
    246c:	ff                   	(bad)  
    246d:	ff                   	(bad)  
    246e:	ff                   	(bad)  
    246f:	ff                   	(bad)  
    2470:	ff                   	(bad)  
    2471:	ff                   	(bad)  
    2472:	ff                   	(bad)  
    2473:	ff                   	(bad)  
    2474:	ff                   	(bad)  
    2475:	ff                   	(bad)  
    2476:	ff                   	(bad)  
    2477:	ff                   	(bad)  
    2478:	ff                   	(bad)  
    2479:	ff                   	(bad)  
    247a:	ff                   	(bad)  
    247b:	ff                   	(bad)  
    247c:	ff                   	(bad)  
    247d:	ff                   	(bad)  
    247e:	ff                   	(bad)  
    247f:	ff                   	(bad)  
    2480:	ff                   	(bad)  
    2481:	ff                   	(bad)  
    2482:	ff                   	(bad)  
    2483:	ff                   	(bad)  
    2484:	ff                   	(bad)  
    2485:	ff                   	(bad)  
    2486:	ff                   	(bad)  
    2487:	ff                   	(bad)  
    2488:	ff                   	(bad)  
    2489:	ff                   	(bad)  
    248a:	ff                   	(bad)  
    248b:	ff                   	(bad)  
    248c:	ff                   	(bad)  
    248d:	ff                   	(bad)  
    248e:	ff                   	(bad)  
    248f:	ff                   	(bad)  
    2490:	ff                   	(bad)  
    2491:	ff                   	(bad)  
    2492:	ff                   	(bad)  
    2493:	ff                   	(bad)  
    2494:	ff                   	(bad)  
    2495:	ff                   	(bad)  
    2496:	ff                   	(bad)  
    2497:	ff                   	(bad)  
    2498:	ff                   	(bad)  
    2499:	ff                   	(bad)  
    249a:	ff                   	(bad)  
    249b:	ff                   	(bad)  
    249c:	ff                   	(bad)  
    249d:	ff                   	(bad)  
    249e:	ff                   	(bad)  
    249f:	ff                   	(bad)  
    24a0:	ff                   	(bad)  
    24a1:	ff                   	(bad)  
    24a2:	ff                   	(bad)  
    24a3:	ff                   	(bad)  
    24a4:	ff                   	(bad)  
    24a5:	ff                   	(bad)  
    24a6:	ff                   	(bad)  
    24a7:	ff                   	(bad)  
    24a8:	ff                   	(bad)  
    24a9:	ff                   	(bad)  
    24aa:	ff                   	(bad)  
    24ab:	ff                   	(bad)  
    24ac:	ff                   	(bad)  
    24ad:	ff                   	(bad)  
    24ae:	ff                   	(bad)  
    24af:	ff                   	(bad)  
    24b0:	ff                   	(bad)  
    24b1:	ff                   	(bad)  
    24b2:	ff                   	(bad)  
    24b3:	ff                   	(bad)  
    24b4:	ff                   	(bad)  
    24b5:	ff                   	(bad)  
    24b6:	ff                   	(bad)  
    24b7:	ff                   	(bad)  
    24b8:	ff                   	(bad)  
    24b9:	ff                   	(bad)  
    24ba:	ff                   	(bad)  
    24bb:	ff                   	(bad)  
    24bc:	ff                   	(bad)  
    24bd:	ff                   	(bad)  
    24be:	ff                   	(bad)  
    24bf:	ff                   	(bad)  
    24c0:	ff                   	(bad)  
    24c1:	ff                   	(bad)  
    24c2:	ff                   	(bad)  
    24c3:	ff                   	(bad)  
    24c4:	ff                   	(bad)  
    24c5:	ff                   	(bad)  
    24c6:	ff                   	(bad)  
    24c7:	ff                   	(bad)  
    24c8:	ff                   	(bad)  
    24c9:	ff                   	(bad)  
    24ca:	ff                   	(bad)  
    24cb:	ff                   	(bad)  
    24cc:	ff                   	(bad)  
    24cd:	ff                   	(bad)  
    24ce:	ff                   	(bad)  
    24cf:	ff                   	(bad)  
    24d0:	ff                   	(bad)  
    24d1:	ff                   	(bad)  
    24d2:	ff                   	(bad)  
    24d3:	ff                   	(bad)  
    24d4:	ff                   	(bad)  
    24d5:	ff                   	(bad)  
    24d6:	ff                   	(bad)  
    24d7:	ff                   	(bad)  
    24d8:	ff                   	(bad)  
    24d9:	ff                   	(bad)  
    24da:	ff                   	(bad)  
    24db:	ff                   	(bad)  
    24dc:	ff                   	(bad)  
    24dd:	ff                   	(bad)  
    24de:	ff                   	(bad)  
    24df:	ff                   	(bad)  
    24e0:	ff                   	(bad)  
    24e1:	ff                   	(bad)  
    24e2:	ff                   	(bad)  
    24e3:	ff                   	(bad)  
    24e4:	ff                   	(bad)  
    24e5:	ff                   	(bad)  
    24e6:	ff                   	(bad)  
    24e7:	ff                   	(bad)  
    24e8:	ff                   	(bad)  
    24e9:	ff                   	(bad)  
    24ea:	ff                   	(bad)  
    24eb:	ff                   	(bad)  
    24ec:	ff                   	(bad)  
    24ed:	ff                   	(bad)  
    24ee:	ff                   	(bad)  
    24ef:	ff                   	(bad)  
    24f0:	ff                   	(bad)  
    24f1:	ff                   	(bad)  
    24f2:	ff                   	(bad)  
    24f3:	ff                   	(bad)  
    24f4:	ff                   	(bad)  
    24f5:	ff                   	(bad)  
    24f6:	ff                   	(bad)  
    24f7:	ff                   	(bad)  
    24f8:	ff                   	(bad)  
    24f9:	ff                   	(bad)  
    24fa:	ff                   	(bad)  
    24fb:	ff                   	(bad)  
    24fc:	ff                   	(bad)  
    24fd:	ff                   	(bad)  
    24fe:	ff                   	(bad)  
    24ff:	ff                   	(bad)  
    2500:	ff                   	(bad)  
    2501:	ff                   	(bad)  
    2502:	ff                   	(bad)  
    2503:	ff                   	(bad)  
    2504:	ff                   	(bad)  
    2505:	ff                   	(bad)  
    2506:	ff                   	(bad)  
    2507:	ff                   	(bad)  
    2508:	ff                   	(bad)  
    2509:	ff                   	(bad)  
    250a:	ff                   	(bad)  
    250b:	ff                   	(bad)  
    250c:	ff                   	(bad)  
    250d:	ff                   	(bad)  
    250e:	ff                   	(bad)  
    250f:	ff                   	(bad)  
    2510:	ff                   	(bad)  
    2511:	ff                   	(bad)  
    2512:	ff                   	(bad)  
    2513:	ff                   	(bad)  
    2514:	ff                   	(bad)  
    2515:	ff                   	(bad)  
    2516:	ff                   	(bad)  
    2517:	ff                   	(bad)  
    2518:	ff                   	(bad)  
    2519:	ff                   	(bad)  
    251a:	ff                   	(bad)  
    251b:	ff                   	(bad)  
    251c:	ff                   	(bad)  
    251d:	ff                   	(bad)  
    251e:	ff                   	(bad)  
    251f:	ff                   	(bad)  
    2520:	ff                   	(bad)  
    2521:	ff                   	(bad)  
    2522:	ff                   	(bad)  
    2523:	ff                   	(bad)  
    2524:	ff                   	(bad)  
    2525:	ff                   	(bad)  
    2526:	ff                   	(bad)  
    2527:	ff                   	(bad)  
    2528:	ff                   	(bad)  
    2529:	ff                   	(bad)  
    252a:	ff                   	(bad)  
    252b:	ff                   	(bad)  
    252c:	ff                   	(bad)  
    252d:	ff                   	(bad)  
    252e:	ff                   	(bad)  
    252f:	ff                   	(bad)  
    2530:	ff                   	(bad)  
    2531:	ff                   	(bad)  
    2532:	ff                   	(bad)  
    2533:	ff                   	(bad)  
    2534:	ff                   	(bad)  
    2535:	ff                   	(bad)  
    2536:	ff                   	(bad)  
    2537:	ff                   	(bad)  
    2538:	ff                   	(bad)  
    2539:	ff                   	(bad)  
    253a:	ff                   	(bad)  
    253b:	ff                   	(bad)  
    253c:	ff                   	(bad)  
    253d:	ff                   	(bad)  
    253e:	ff                   	(bad)  
    253f:	ff                   	(bad)  
    2540:	ff                   	(bad)  
    2541:	ff                   	(bad)  
    2542:	ff                   	(bad)  
    2543:	ff                   	(bad)  
    2544:	ff                   	(bad)  
    2545:	ff                   	(bad)  
    2546:	ff                   	(bad)  
    2547:	ff                   	(bad)  
    2548:	ff                   	(bad)  
    2549:	ff                   	(bad)  
    254a:	ff                   	(bad)  
    254b:	ff                   	(bad)  
    254c:	ff                   	(bad)  
    254d:	ff                   	(bad)  
    254e:	ff                   	(bad)  
    254f:	ff                   	(bad)  
    2550:	ff                   	(bad)  
    2551:	ff                   	(bad)  
    2552:	ff                   	(bad)  
    2553:	ff                   	(bad)  
    2554:	ff                   	(bad)  
    2555:	ff                   	(bad)  
    2556:	ff                   	(bad)  
    2557:	ff                   	(bad)  
    2558:	ff                   	(bad)  
    2559:	ff                   	(bad)  
    255a:	ff                   	(bad)  
    255b:	ff                   	(bad)  
    255c:	ff                   	(bad)  
    255d:	ff                   	(bad)  
    255e:	ff                   	(bad)  
    255f:	ff                   	(bad)  
    2560:	ff                   	(bad)  
    2561:	ff                   	(bad)  
    2562:	ff                   	(bad)  
    2563:	ff                   	(bad)  
    2564:	ff                   	(bad)  
    2565:	ff                   	(bad)  
    2566:	ff                   	(bad)  
    2567:	ff                   	(bad)  
    2568:	ff                   	(bad)  
    2569:	ff                   	(bad)  
    256a:	ff                   	(bad)  
    256b:	ff                   	(bad)  
    256c:	ff                   	(bad)  
    256d:	ff                   	(bad)  
    256e:	ff                   	(bad)  
    256f:	ff                   	(bad)  
    2570:	ff                   	(bad)  
    2571:	ff                   	(bad)  
    2572:	ff                   	(bad)  
    2573:	ff                   	(bad)  
    2574:	ff                   	(bad)  
    2575:	ff                   	(bad)  
    2576:	ff                   	(bad)  
    2577:	ff                   	(bad)  
    2578:	ff                   	(bad)  
    2579:	ff                   	(bad)  
    257a:	ff                   	(bad)  
    257b:	ff                   	(bad)  
    257c:	ff                   	(bad)  
    257d:	ff                   	(bad)  
    257e:	ff                   	(bad)  
    257f:	ff                   	(bad)  
    2580:	ff                   	(bad)  
    2581:	ff                   	(bad)  
    2582:	ff                   	(bad)  
    2583:	ff                   	(bad)  
    2584:	ff                   	(bad)  
    2585:	ff                   	(bad)  
    2586:	ff                   	(bad)  
    2587:	ff                   	(bad)  
    2588:	ff                   	(bad)  
    2589:	ff                   	(bad)  
    258a:	ff                   	(bad)  
    258b:	ff                   	(bad)  
    258c:	ff                   	(bad)  
    258d:	ff                   	(bad)  
    258e:	ff                   	(bad)  
    258f:	ff                   	(bad)  
    2590:	ff                   	(bad)  
    2591:	ff                   	(bad)  
    2592:	ff                   	(bad)  
    2593:	ff                   	(bad)  
    2594:	ff                   	(bad)  
    2595:	ff                   	(bad)  
    2596:	ff                   	(bad)  
    2597:	ff                   	(bad)  
    2598:	ff                   	(bad)  
    2599:	ff                   	(bad)  
    259a:	ff                   	(bad)  
    259b:	ff                   	(bad)  
    259c:	ff                   	(bad)  
    259d:	ff                   	(bad)  
    259e:	ff                   	(bad)  
    259f:	ff                   	(bad)  
    25a0:	ff                   	(bad)  
    25a1:	ff                   	(bad)  
    25a2:	ff                   	(bad)  
    25a3:	ff                   	(bad)  
    25a4:	ff                   	(bad)  
    25a5:	ff                   	(bad)  
    25a6:	ff                   	(bad)  
    25a7:	ff                   	(bad)  
    25a8:	ff                   	(bad)  
    25a9:	ff                   	(bad)  
    25aa:	ff                   	(bad)  
    25ab:	ff                   	(bad)  
    25ac:	ff                   	(bad)  
    25ad:	ff                   	(bad)  
    25ae:	ff                   	(bad)  
    25af:	ff                   	(bad)  
    25b0:	ff                   	(bad)  
    25b1:	ff                   	(bad)  
    25b2:	ff                   	(bad)  
    25b3:	ff                   	(bad)  
    25b4:	ff                   	(bad)  
    25b5:	ff                   	(bad)  
    25b6:	ff                   	(bad)  
    25b7:	ff                   	(bad)  
    25b8:	ff                   	(bad)  
    25b9:	ff                   	(bad)  
    25ba:	ff                   	(bad)  
    25bb:	ff                   	(bad)  
    25bc:	ff                   	(bad)  
    25bd:	ff                   	(bad)  
    25be:	ff                   	(bad)  
    25bf:	ff                   	(bad)  
    25c0:	ff                   	(bad)  
    25c1:	ff                   	(bad)  
    25c2:	ff                   	(bad)  
    25c3:	ff                   	(bad)  
    25c4:	ff                   	(bad)  
    25c5:	ff                   	(bad)  
    25c6:	ff                   	(bad)  
    25c7:	ff                   	(bad)  
    25c8:	ff                   	(bad)  
    25c9:	ff                   	(bad)  
    25ca:	ff                   	(bad)  
    25cb:	ff                   	(bad)  
    25cc:	ff                   	(bad)  
    25cd:	ff                   	(bad)  
    25ce:	ff                   	(bad)  
    25cf:	ff                   	(bad)  
    25d0:	ff                   	(bad)  
    25d1:	ff                   	(bad)  
    25d2:	ff                   	(bad)  
    25d3:	ff                   	(bad)  
    25d4:	ff                   	(bad)  
    25d5:	ff                   	(bad)  
    25d6:	ff                   	(bad)  
    25d7:	ff                   	(bad)  
    25d8:	ff                   	(bad)  
    25d9:	ff                   	(bad)  
    25da:	ff                   	(bad)  
    25db:	ff                   	(bad)  
    25dc:	ff                   	(bad)  
    25dd:	ff                   	(bad)  
    25de:	ff                   	(bad)  
    25df:	ff                   	(bad)  
    25e0:	ff                   	(bad)  
    25e1:	ff                   	(bad)  
    25e2:	ff                   	(bad)  
    25e3:	ff                   	(bad)  
    25e4:	ff                   	(bad)  
    25e5:	ff                   	(bad)  
    25e6:	ff                   	(bad)  
    25e7:	ff                   	(bad)  
    25e8:	ff                   	(bad)  
    25e9:	ff                   	(bad)  
    25ea:	ff                   	(bad)  
    25eb:	ff                   	(bad)  
    25ec:	ff                   	(bad)  
    25ed:	ff                   	(bad)  
    25ee:	ff                   	(bad)  
    25ef:	ff                   	(bad)  
    25f0:	ff                   	(bad)  
    25f1:	ff                   	(bad)  
    25f2:	ff                   	(bad)  
    25f3:	ff                   	(bad)  
    25f4:	ff                   	(bad)  
    25f5:	ff                   	(bad)  
    25f6:	ff                   	(bad)  
    25f7:	ff                   	(bad)  
    25f8:	ff                   	(bad)  
    25f9:	ff                   	(bad)  
    25fa:	ff                   	(bad)  
    25fb:	ff                   	(bad)  
    25fc:	ff                   	(bad)  
    25fd:	ff                   	(bad)  
    25fe:	ff                   	(bad)  
    25ff:	ff                   	(bad)  
    2600:	ff                   	(bad)  
    2601:	ff                   	(bad)  
    2602:	ff                   	(bad)  
    2603:	ff                   	(bad)  
    2604:	ff                   	(bad)  
    2605:	ff                   	(bad)  
    2606:	ff                   	(bad)  
    2607:	ff                   	(bad)  
    2608:	ff                   	(bad)  
    2609:	ff                   	(bad)  
    260a:	ff                   	(bad)  
    260b:	ff                   	(bad)  
    260c:	ff                   	(bad)  
    260d:	ff                   	(bad)  
    260e:	ff                   	(bad)  
    260f:	ff                   	(bad)  
    2610:	ff                   	(bad)  
    2611:	ff                   	(bad)  
    2612:	ff                   	(bad)  
    2613:	ff                   	(bad)  
    2614:	ff                   	(bad)  
    2615:	ff                   	(bad)  
    2616:	ff                   	(bad)  
    2617:	ff                   	(bad)  
    2618:	ff                   	(bad)  
    2619:	ff                   	(bad)  
    261a:	ff                   	(bad)  
    261b:	ff                   	(bad)  
    261c:	ff                   	(bad)  
    261d:	ff                   	(bad)  
    261e:	ff                   	(bad)  
    261f:	ff                   	(bad)  
    2620:	ff                   	(bad)  
    2621:	ff                   	(bad)  
    2622:	ff                   	(bad)  
    2623:	ff                   	(bad)  
    2624:	ff                   	(bad)  
    2625:	ff                   	(bad)  
    2626:	ff                   	(bad)  
    2627:	ff                   	(bad)  
    2628:	ff                   	(bad)  
    2629:	ff                   	(bad)  
    262a:	ff                   	(bad)  
    262b:	ff                   	(bad)  
    262c:	ff                   	(bad)  
    262d:	ff                   	(bad)  
    262e:	ff                   	(bad)  
    262f:	ff                   	(bad)  
    2630:	ff                   	(bad)  
    2631:	ff                   	(bad)  
    2632:	ff                   	(bad)  
    2633:	ff                   	(bad)  
    2634:	ff                   	(bad)  
    2635:	ff                   	(bad)  
    2636:	ff                   	(bad)  
    2637:	ff                   	(bad)  
    2638:	ff                   	(bad)  
    2639:	ff                   	(bad)  
    263a:	ff                   	(bad)  
    263b:	ff                   	(bad)  
    263c:	ff                   	(bad)  
    263d:	ff                   	(bad)  
    263e:	ff                   	(bad)  
    263f:	ff                   	(bad)  
    2640:	ff                   	(bad)  
    2641:	ff                   	(bad)  
    2642:	ff                   	(bad)  
    2643:	ff                   	(bad)  
    2644:	ff                   	(bad)  
    2645:	ff                   	(bad)  
    2646:	ff                   	(bad)  
    2647:	ff                   	(bad)  
    2648:	ff                   	(bad)  
    2649:	ff                   	(bad)  
    264a:	ff                   	(bad)  
    264b:	ff                   	(bad)  
    264c:	ff                   	(bad)  
    264d:	ff                   	(bad)  
    264e:	ff                   	(bad)  
    264f:	ff                   	(bad)  
    2650:	ff                   	(bad)  
    2651:	ff                   	(bad)  
    2652:	ff                   	(bad)  
    2653:	ff                   	(bad)  
    2654:	ff                   	(bad)  
    2655:	ff                   	(bad)  
    2656:	ff                   	(bad)  
    2657:	ff                   	(bad)  
    2658:	ff                   	(bad)  
    2659:	ff                   	(bad)  
    265a:	ff                   	(bad)  
    265b:	ff                   	(bad)  
    265c:	ff                   	(bad)  
    265d:	ff                   	(bad)  
    265e:	ff                   	(bad)  
    265f:	ff                   	(bad)  
    2660:	ff                   	(bad)  
    2661:	ff                   	(bad)  
    2662:	ff                   	(bad)  
    2663:	ff                   	(bad)  
    2664:	ff                   	(bad)  
    2665:	ff                   	(bad)  
    2666:	ff                   	(bad)  
    2667:	ff                   	(bad)  
    2668:	ff                   	(bad)  
    2669:	ff                   	(bad)  
    266a:	ff                   	(bad)  
    266b:	ff                   	(bad)  
    266c:	ff                   	(bad)  
    266d:	ff                   	(bad)  
    266e:	ff                   	(bad)  
    266f:	ff                   	(bad)  
    2670:	ff                   	(bad)  
    2671:	ff                   	(bad)  
    2672:	ff                   	(bad)  
    2673:	ff                   	(bad)  
    2674:	ff                   	(bad)  
    2675:	ff                   	(bad)  
    2676:	ff                   	(bad)  
    2677:	ff                   	(bad)  
    2678:	ff                   	(bad)  
    2679:	ff                   	(bad)  
    267a:	ff                   	(bad)  
    267b:	ff                   	(bad)  
    267c:	ff                   	(bad)  
    267d:	ff                   	(bad)  
    267e:	ff                   	(bad)  
    267f:	ff                   	(bad)  
    2680:	ff                   	(bad)  
    2681:	ff                   	(bad)  
    2682:	ff                   	(bad)  
    2683:	ff                   	(bad)  
    2684:	ff                   	(bad)  
    2685:	ff                   	(bad)  
    2686:	ff                   	(bad)  
    2687:	ff                   	(bad)  
    2688:	ff                   	(bad)  
    2689:	ff                   	(bad)  
    268a:	ff                   	(bad)  
    268b:	ff                   	(bad)  
    268c:	ff                   	(bad)  
    268d:	ff                   	(bad)  
    268e:	ff                   	(bad)  
    268f:	ff                   	(bad)  
    2690:	ff                   	(bad)  
    2691:	ff                   	(bad)  
    2692:	ff                   	(bad)  
    2693:	ff                   	(bad)  
    2694:	ff                   	(bad)  
    2695:	ff                   	(bad)  
    2696:	ff                   	(bad)  
    2697:	ff                   	(bad)  
    2698:	ff                   	(bad)  
    2699:	ff                   	(bad)  
    269a:	ff                   	(bad)  
    269b:	ff                   	(bad)  
    269c:	ff                   	(bad)  
    269d:	ff                   	(bad)  
    269e:	ff                   	(bad)  
    269f:	ff                   	(bad)  
    26a0:	ff                   	(bad)  
    26a1:	ff                   	(bad)  
    26a2:	ff                   	(bad)  
    26a3:	ff                   	(bad)  
    26a4:	ff                   	(bad)  
    26a5:	ff                   	(bad)  
    26a6:	ff                   	(bad)  
    26a7:	ff                   	(bad)  
    26a8:	ff                   	(bad)  
    26a9:	ff                   	(bad)  
    26aa:	ff                   	(bad)  
    26ab:	ff                   	(bad)  
    26ac:	ff                   	(bad)  
    26ad:	ff                   	(bad)  
    26ae:	ff                   	(bad)  
    26af:	ff                   	(bad)  
    26b0:	ff                   	(bad)  
    26b1:	ff                   	(bad)  
    26b2:	ff                   	(bad)  
    26b3:	ff                   	(bad)  
    26b4:	ff                   	(bad)  
    26b5:	ff                   	(bad)  
    26b6:	ff                   	(bad)  
    26b7:	ff                   	(bad)  
    26b8:	ff                   	(bad)  
    26b9:	ff                   	(bad)  
    26ba:	ff                   	(bad)  
    26bb:	ff                   	(bad)  
    26bc:	ff                   	(bad)  
    26bd:	ff                   	(bad)  
    26be:	ff                   	(bad)  
    26bf:	ff                   	(bad)  
    26c0:	ff                   	(bad)  
    26c1:	ff                   	(bad)  
    26c2:	ff                   	(bad)  
    26c3:	ff                   	(bad)  
    26c4:	ff                   	(bad)  
    26c5:	ff                   	(bad)  
    26c6:	ff                   	(bad)  
    26c7:	ff                   	(bad)  
    26c8:	ff                   	(bad)  
    26c9:	ff                   	(bad)  
    26ca:	ff                   	(bad)  
    26cb:	ff                   	(bad)  
    26cc:	ff                   	(bad)  
    26cd:	ff                   	(bad)  
    26ce:	ff                   	(bad)  
    26cf:	ff                   	(bad)  
    26d0:	ff                   	(bad)  
    26d1:	ff                   	(bad)  
    26d2:	ff                   	(bad)  
    26d3:	ff                   	(bad)  
    26d4:	ff                   	(bad)  
    26d5:	ff                   	(bad)  
    26d6:	ff                   	(bad)  
    26d7:	ff                   	(bad)  
    26d8:	ff                   	(bad)  
    26d9:	ff                   	(bad)  
    26da:	ff                   	(bad)  
    26db:	ff                   	(bad)  
    26dc:	ff                   	(bad)  
    26dd:	ff                   	(bad)  
    26de:	ff                   	(bad)  
    26df:	ff                   	(bad)  
    26e0:	ff                   	(bad)  
    26e1:	ff                   	(bad)  
    26e2:	ff                   	(bad)  
    26e3:	ff                   	(bad)  
    26e4:	ff                   	(bad)  
    26e5:	ff                   	(bad)  
    26e6:	ff                   	(bad)  
    26e7:	ff                   	(bad)  
    26e8:	ff                   	(bad)  
    26e9:	ff                   	(bad)  
    26ea:	ff                   	(bad)  
    26eb:	ff                   	(bad)  
    26ec:	ff                   	(bad)  
    26ed:	ff                   	(bad)  
    26ee:	ff                   	(bad)  
    26ef:	ff                   	(bad)  
    26f0:	ff                   	(bad)  
    26f1:	ff                   	(bad)  
    26f2:	ff                   	(bad)  
    26f3:	ff                   	(bad)  
    26f4:	ff                   	(bad)  
    26f5:	ff                   	(bad)  
    26f6:	ff                   	(bad)  
    26f7:	ff                   	(bad)  
    26f8:	ff                   	(bad)  
    26f9:	ff                   	(bad)  
    26fa:	ff                   	(bad)  
    26fb:	ff                   	(bad)  
    26fc:	ff                   	(bad)  
    26fd:	ff                   	(bad)  
    26fe:	ff                   	(bad)  
    26ff:	ff                   	(bad)  
    2700:	ff                   	(bad)  
    2701:	ff                   	(bad)  
    2702:	ff                   	(bad)  
    2703:	ff                   	(bad)  
    2704:	ff                   	(bad)  
    2705:	ff                   	(bad)  
    2706:	ff                   	(bad)  
    2707:	ff                   	(bad)  
    2708:	ff                   	(bad)  
    2709:	ff                   	(bad)  
    270a:	ff                   	(bad)  
    270b:	ff                   	(bad)  
    270c:	ff                   	(bad)  
    270d:	ff                   	(bad)  
    270e:	ff                   	(bad)  
    270f:	ff                   	(bad)  
    2710:	ff                   	(bad)  
    2711:	ff                   	(bad)  
    2712:	ff                   	(bad)  
    2713:	ff                   	(bad)  
    2714:	ff                   	(bad)  
    2715:	ff                   	(bad)  
    2716:	ff                   	(bad)  
    2717:	ff                   	(bad)  
    2718:	ff                   	(bad)  
    2719:	ff                   	(bad)  
    271a:	ff                   	(bad)  
    271b:	ff                   	(bad)  
    271c:	ff                   	(bad)  
    271d:	ff                   	(bad)  
    271e:	ff                   	(bad)  
    271f:	ff                   	(bad)  
    2720:	ff                   	(bad)  
    2721:	ff                   	(bad)  
    2722:	ff                   	(bad)  
    2723:	ff                   	(bad)  
    2724:	ff                   	(bad)  
    2725:	ff                   	(bad)  
    2726:	ff                   	(bad)  
    2727:	ff                   	(bad)  
    2728:	ff                   	(bad)  
    2729:	ff                   	(bad)  
    272a:	ff                   	(bad)  
    272b:	ff                   	(bad)  
    272c:	ff                   	(bad)  
    272d:	ff                   	(bad)  
    272e:	ff                   	(bad)  
    272f:	ff                   	(bad)  
    2730:	ff                   	(bad)  
    2731:	ff                   	(bad)  
    2732:	ff                   	(bad)  
    2733:	ff                   	(bad)  
    2734:	ff                   	(bad)  
    2735:	ff                   	(bad)  
    2736:	ff                   	(bad)  
    2737:	ff                   	(bad)  
    2738:	ff                   	(bad)  
    2739:	ff                   	(bad)  
    273a:	ff                   	(bad)  
    273b:	ff                   	(bad)  
    273c:	ff                   	(bad)  
    273d:	ff                   	(bad)  
    273e:	ff                   	(bad)  
    273f:	ff                   	(bad)  
    2740:	ff                   	(bad)  
    2741:	ff                   	(bad)  
    2742:	ff                   	(bad)  
    2743:	ff                   	(bad)  
    2744:	ff                   	(bad)  
    2745:	ff                   	(bad)  
    2746:	ff                   	(bad)  
    2747:	ff                   	(bad)  
    2748:	ff                   	(bad)  
    2749:	ff                   	(bad)  
    274a:	ff                   	(bad)  
    274b:	ff                   	(bad)  
    274c:	ff                   	(bad)  
    274d:	ff                   	(bad)  
    274e:	ff                   	(bad)  
    274f:	ff                   	(bad)  
    2750:	ff                   	(bad)  
    2751:	ff                   	(bad)  
    2752:	ff                   	(bad)  
    2753:	ff                   	(bad)  
    2754:	ff                   	(bad)  
    2755:	ff                   	(bad)  
    2756:	ff                   	(bad)  
    2757:	ff                   	(bad)  
    2758:	ff                   	(bad)  
    2759:	ff                   	(bad)  
    275a:	ff                   	(bad)  
    275b:	ff                   	(bad)  
    275c:	ff                   	(bad)  
    275d:	ff                   	(bad)  
    275e:	ff                   	(bad)  
    275f:	ff                   	(bad)  
    2760:	ff                   	(bad)  
    2761:	ff                   	(bad)  
    2762:	ff                   	(bad)  
    2763:	ff                   	(bad)  
    2764:	ff                   	(bad)  
    2765:	ff                   	(bad)  
    2766:	ff                   	(bad)  
    2767:	ff                   	(bad)  
    2768:	ff                   	(bad)  
    2769:	ff                   	(bad)  
    276a:	ff                   	(bad)  
    276b:	ff                   	(bad)  
    276c:	ff                   	(bad)  
    276d:	ff                   	(bad)  
    276e:	ff                   	(bad)  
    276f:	ff                   	(bad)  
    2770:	ff                   	(bad)  
    2771:	ff                   	(bad)  
    2772:	ff                   	(bad)  
    2773:	ff                   	(bad)  
    2774:	ff                   	(bad)  
    2775:	ff                   	(bad)  
    2776:	ff                   	(bad)  
    2777:	ff                   	(bad)  
    2778:	ff                   	(bad)  
    2779:	ff                   	(bad)  
    277a:	ff                   	(bad)  
    277b:	ff                   	(bad)  
    277c:	ff                   	(bad)  
    277d:	ff                   	(bad)  
    277e:	ff                   	(bad)  
    277f:	ff                   	(bad)  
    2780:	ff                   	(bad)  
    2781:	ff                   	(bad)  
    2782:	ff                   	(bad)  
    2783:	ff                   	(bad)  
    2784:	ff                   	(bad)  
    2785:	ff                   	(bad)  
    2786:	ff                   	(bad)  
    2787:	ff                   	(bad)  
    2788:	ff                   	(bad)  
    2789:	ff                   	(bad)  
    278a:	ff                   	(bad)  
    278b:	ff                   	(bad)  
    278c:	ff                   	(bad)  
    278d:	ff                   	(bad)  
    278e:	ff                   	(bad)  
    278f:	ff                   	(bad)  
    2790:	ff                   	(bad)  
    2791:	ff                   	(bad)  
    2792:	ff                   	(bad)  
    2793:	ff                   	(bad)  
    2794:	ff                   	(bad)  
    2795:	ff                   	(bad)  
    2796:	ff                   	(bad)  
    2797:	ff                   	(bad)  
    2798:	ff                   	(bad)  
    2799:	ff                   	(bad)  
    279a:	ff                   	(bad)  
    279b:	ff                   	(bad)  
    279c:	ff                   	(bad)  
    279d:	ff                   	(bad)  
    279e:	ff                   	(bad)  
    279f:	ff                   	(bad)  
    27a0:	ff                   	(bad)  
    27a1:	ff                   	(bad)  
    27a2:	ff                   	(bad)  
    27a3:	ff                   	(bad)  
    27a4:	ff                   	(bad)  
    27a5:	ff                   	(bad)  
    27a6:	ff                   	(bad)  
    27a7:	ff                   	(bad)  
    27a8:	ff                   	(bad)  
    27a9:	ff                   	(bad)  
    27aa:	ff                   	(bad)  
    27ab:	ff                   	(bad)  
    27ac:	ff                   	(bad)  
    27ad:	ff                   	(bad)  
    27ae:	ff                   	(bad)  
    27af:	ff                   	(bad)  
    27b0:	ff                   	(bad)  
    27b1:	ff                   	(bad)  
    27b2:	ff                   	(bad)  
    27b3:	ff                   	(bad)  
    27b4:	ff                   	(bad)  
    27b5:	ff                   	(bad)  
    27b6:	ff                   	(bad)  
    27b7:	ff                   	(bad)  
    27b8:	ff                   	(bad)  
    27b9:	ff                   	(bad)  
    27ba:	ff                   	(bad)  
    27bb:	ff                   	(bad)  
    27bc:	ff                   	(bad)  
    27bd:	ff                   	(bad)  
    27be:	ff                   	(bad)  
    27bf:	ff                   	(bad)  
    27c0:	ff                   	(bad)  
    27c1:	ff                   	(bad)  
    27c2:	ff                   	(bad)  
    27c3:	ff                   	(bad)  
    27c4:	ff                   	(bad)  
    27c5:	ff                   	(bad)  
    27c6:	ff                   	(bad)  
    27c7:	ff                   	(bad)  
    27c8:	ff                   	(bad)  
    27c9:	ff                   	(bad)  
    27ca:	ff                   	(bad)  
    27cb:	ff                   	(bad)  
    27cc:	ff                   	(bad)  
    27cd:	ff                   	(bad)  
    27ce:	ff                   	(bad)  
    27cf:	ff                   	(bad)  
    27d0:	ff                   	(bad)  
    27d1:	ff                   	(bad)  
    27d2:	ff                   	(bad)  
    27d3:	ff                   	(bad)  
    27d4:	ff                   	(bad)  
    27d5:	ff                   	(bad)  
    27d6:	ff                   	(bad)  
    27d7:	ff                   	(bad)  
    27d8:	ff                   	(bad)  
    27d9:	ff                   	(bad)  
    27da:	ff                   	(bad)  
    27db:	ff                   	(bad)  
    27dc:	ff                   	(bad)  
    27dd:	ff                   	(bad)  
    27de:	ff                   	(bad)  
    27df:	ff                   	(bad)  
    27e0:	ff                   	(bad)  
    27e1:	ff                   	(bad)  
    27e2:	ff                   	(bad)  
    27e3:	ff                   	(bad)  
    27e4:	ff                   	(bad)  
    27e5:	ff                   	(bad)  
    27e6:	ff                   	(bad)  
    27e7:	ff                   	(bad)  
    27e8:	ff                   	(bad)  
    27e9:	ff                   	(bad)  
    27ea:	ff                   	(bad)  
    27eb:	ff                   	(bad)  
    27ec:	ff                   	(bad)  
    27ed:	ff                   	(bad)  
    27ee:	ff                   	(bad)  
    27ef:	ff                   	(bad)  
    27f0:	ff                   	(bad)  
    27f1:	ff                   	(bad)  
    27f2:	ff                   	(bad)  
    27f3:	ff                   	(bad)  
    27f4:	ff                   	(bad)  
    27f5:	ff                   	(bad)  
    27f6:	ff                   	(bad)  
    27f7:	ff                   	(bad)  
    27f8:	ff                   	(bad)  
    27f9:	ff                   	(bad)  
    27fa:	ff                   	(bad)  
    27fb:	ff                   	(bad)  
    27fc:	ff                   	(bad)  
    27fd:	ff                   	(bad)  
    27fe:	ff                   	(bad)  
    27ff:	ff                   	(bad)  
    2800:	ff                   	(bad)  
    2801:	ff                   	(bad)  
    2802:	ff                   	(bad)  
    2803:	ff                   	(bad)  
    2804:	ff                   	(bad)  
    2805:	ff                   	(bad)  
    2806:	ff                   	(bad)  
    2807:	ff                   	(bad)  
    2808:	ff                   	(bad)  
    2809:	ff                   	(bad)  
    280a:	ff                   	(bad)  
    280b:	ff                   	(bad)  
    280c:	ff                   	(bad)  
    280d:	ff                   	(bad)  
    280e:	ff                   	(bad)  
    280f:	ff                   	(bad)  
    2810:	ff                   	(bad)  
    2811:	ff                   	(bad)  
    2812:	ff                   	(bad)  
    2813:	ff                   	(bad)  
    2814:	ff                   	(bad)  
    2815:	ff                   	(bad)  
    2816:	ff                   	(bad)  
    2817:	ff                   	(bad)  
    2818:	ff                   	(bad)  
    2819:	ff                   	(bad)  
    281a:	ff                   	(bad)  
    281b:	ff                   	(bad)  
    281c:	ff                   	(bad)  
    281d:	ff                   	(bad)  
    281e:	ff                   	(bad)  
    281f:	ff                   	(bad)  
    2820:	ff                   	(bad)  
    2821:	ff                   	(bad)  
    2822:	ff                   	(bad)  
    2823:	ff                   	(bad)  
    2824:	ff                   	(bad)  
    2825:	ff                   	(bad)  
    2826:	ff                   	(bad)  
    2827:	ff                   	(bad)  
    2828:	ff                   	(bad)  
    2829:	ff                   	(bad)  
    282a:	ff                   	(bad)  
    282b:	ff                   	(bad)  
    282c:	ff                   	(bad)  
    282d:	ff                   	(bad)  
    282e:	ff                   	(bad)  
    282f:	ff                   	(bad)  
    2830:	ff                   	(bad)  
    2831:	ff                   	(bad)  
    2832:	ff                   	(bad)  
    2833:	ff                   	(bad)  
    2834:	ff                   	(bad)  
    2835:	ff                   	(bad)  
    2836:	ff                   	(bad)  
    2837:	ff                   	(bad)  
    2838:	ff                   	(bad)  
    2839:	ff                   	(bad)  
    283a:	ff                   	(bad)  
    283b:	ff                   	(bad)  
    283c:	ff                   	(bad)  
    283d:	ff                   	(bad)  
    283e:	ff                   	(bad)  
    283f:	ff                   	(bad)  
    2840:	ff                   	(bad)  
    2841:	ff                   	(bad)  
    2842:	ff                   	(bad)  
    2843:	ff                   	(bad)  
    2844:	ff                   	(bad)  
    2845:	ff                   	(bad)  
    2846:	ff                   	(bad)  
    2847:	ff                   	(bad)  
    2848:	ff                   	(bad)  
    2849:	ff                   	(bad)  
    284a:	ff                   	(bad)  
    284b:	ff                   	(bad)  
    284c:	ff                   	(bad)  
    284d:	ff                   	(bad)  
    284e:	ff                   	(bad)  
    284f:	ff                   	(bad)  
    2850:	ff                   	(bad)  
    2851:	ff                   	(bad)  
    2852:	ff                   	(bad)  
    2853:	ff                   	(bad)  
    2854:	ff                   	(bad)  
    2855:	ff                   	(bad)  
    2856:	ff                   	(bad)  
    2857:	ff                   	(bad)  
    2858:	ff                   	(bad)  
    2859:	ff                   	(bad)  
    285a:	ff                   	(bad)  
    285b:	ff                   	(bad)  
    285c:	ff                   	(bad)  
    285d:	ff                   	(bad)  
    285e:	ff                   	(bad)  
    285f:	ff                   	(bad)  
    2860:	ff                   	(bad)  
    2861:	ff                   	(bad)  
    2862:	ff                   	(bad)  
    2863:	ff                   	(bad)  
    2864:	ff                   	(bad)  
    2865:	ff                   	(bad)  
    2866:	ff                   	(bad)  
    2867:	ff                   	(bad)  
    2868:	ff                   	(bad)  
    2869:	ff                   	(bad)  
    286a:	ff                   	(bad)  
    286b:	ff                   	(bad)  
    286c:	ff                   	(bad)  
    286d:	ff                   	(bad)  
    286e:	ff                   	(bad)  
    286f:	ff                   	(bad)  
    2870:	ff                   	(bad)  
    2871:	ff                   	(bad)  
    2872:	ff                   	(bad)  
    2873:	ff                   	(bad)  
    2874:	ff                   	(bad)  
    2875:	ff                   	(bad)  
    2876:	ff                   	(bad)  
    2877:	ff                   	(bad)  
    2878:	ff                   	(bad)  
    2879:	ff                   	(bad)  
    287a:	ff                   	(bad)  
    287b:	ff                   	(bad)  
    287c:	ff                   	(bad)  
    287d:	ff                   	(bad)  
    287e:	ff                   	(bad)  
    287f:	ff                   	(bad)  
    2880:	ff                   	(bad)  
    2881:	ff                   	(bad)  
    2882:	ff                   	(bad)  
    2883:	ff                   	(bad)  
    2884:	ff                   	(bad)  
    2885:	ff                   	(bad)  
    2886:	ff                   	(bad)  
    2887:	ff                   	(bad)  
    2888:	ff                   	(bad)  
    2889:	ff                   	(bad)  
    288a:	ff                   	(bad)  
    288b:	ff                   	(bad)  
    288c:	ff                   	(bad)  
    288d:	ff                   	(bad)  
    288e:	ff                   	(bad)  
    288f:	ff                   	(bad)  
    2890:	ff                   	(bad)  
    2891:	ff                   	(bad)  
    2892:	ff                   	(bad)  
    2893:	ff                   	(bad)  
    2894:	ff                   	(bad)  
    2895:	ff                   	(bad)  
    2896:	ff                   	(bad)  
    2897:	ff                   	(bad)  
    2898:	ff                   	(bad)  
    2899:	ff                   	(bad)  
    289a:	ff                   	(bad)  
    289b:	ff                   	(bad)  
    289c:	ff                   	(bad)  
    289d:	ff                   	(bad)  
    289e:	ff                   	(bad)  
    289f:	ff                   	(bad)  
    28a0:	ff                   	(bad)  
    28a1:	ff                   	(bad)  
    28a2:	ff                   	(bad)  
    28a3:	ff                   	(bad)  
    28a4:	ff                   	(bad)  
    28a5:	ff                   	(bad)  
    28a6:	ff                   	(bad)  
    28a7:	ff                   	(bad)  
    28a8:	ff                   	(bad)  
    28a9:	ff                   	(bad)  
    28aa:	ff                   	(bad)  
    28ab:	ff                   	(bad)  
    28ac:	ff                   	(bad)  
    28ad:	ff                   	(bad)  
    28ae:	ff                   	(bad)  
    28af:	ff                   	(bad)  
    28b0:	ff                   	(bad)  
    28b1:	ff                   	(bad)  
    28b2:	ff                   	(bad)  
    28b3:	ff                   	(bad)  
    28b4:	ff                   	(bad)  
    28b5:	ff                   	(bad)  
    28b6:	ff                   	(bad)  
    28b7:	ff                   	(bad)  
    28b8:	ff                   	(bad)  
    28b9:	ff                   	(bad)  
    28ba:	ff                   	(bad)  
    28bb:	ff                   	(bad)  
    28bc:	ff                   	(bad)  
    28bd:	ff                   	(bad)  
    28be:	ff                   	(bad)  
    28bf:	ff                   	(bad)  
    28c0:	ff                   	(bad)  
    28c1:	ff                   	(bad)  
    28c2:	ff                   	(bad)  
    28c3:	ff                   	(bad)  
    28c4:	ff                   	(bad)  
    28c5:	ff                   	(bad)  
    28c6:	ff                   	(bad)  
    28c7:	ff                   	(bad)  
    28c8:	ff                   	(bad)  
    28c9:	ff                   	(bad)  
    28ca:	ff                   	(bad)  
    28cb:	ff                   	(bad)  
    28cc:	ff                   	(bad)  
    28cd:	ff                   	(bad)  
    28ce:	ff                   	(bad)  
    28cf:	ff                   	(bad)  
    28d0:	ff                   	(bad)  
    28d1:	ff                   	(bad)  
    28d2:	ff                   	(bad)  
    28d3:	ff                   	(bad)  
    28d4:	ff                   	(bad)  
    28d5:	ff                   	(bad)  
    28d6:	ff                   	(bad)  
    28d7:	ff                   	(bad)  
    28d8:	ff                   	(bad)  
    28d9:	ff                   	(bad)  
    28da:	ff                   	(bad)  
    28db:	ff                   	(bad)  
    28dc:	ff                   	(bad)  
    28dd:	ff                   	(bad)  
    28de:	ff                   	(bad)  
    28df:	ff                   	(bad)  
    28e0:	ff                   	(bad)  
    28e1:	ff                   	(bad)  
    28e2:	ff                   	(bad)  
    28e3:	ff                   	(bad)  
    28e4:	ff                   	(bad)  
    28e5:	ff                   	(bad)  
    28e6:	ff                   	(bad)  
    28e7:	ff                   	(bad)  
    28e8:	ff                   	(bad)  
    28e9:	ff                   	(bad)  
    28ea:	ff                   	(bad)  
    28eb:	ff                   	(bad)  
    28ec:	ff                   	(bad)  
    28ed:	ff                   	(bad)  
    28ee:	ff                   	(bad)  
    28ef:	ff                   	(bad)  
    28f0:	ff                   	(bad)  
    28f1:	ff                   	(bad)  
    28f2:	ff                   	(bad)  
    28f3:	ff                   	(bad)  
    28f4:	ff                   	(bad)  
    28f5:	ff                   	(bad)  
    28f6:	ff                   	(bad)  
    28f7:	ff                   	(bad)  
    28f8:	ff                   	(bad)  
    28f9:	ff                   	(bad)  
    28fa:	ff                   	(bad)  
    28fb:	ff                   	(bad)  
    28fc:	ff                   	(bad)  
    28fd:	ff                   	(bad)  
    28fe:	ff                   	(bad)  
    28ff:	ff                   	(bad)  
    2900:	ff                   	(bad)  
    2901:	ff                   	(bad)  
    2902:	ff                   	(bad)  
    2903:	ff                   	(bad)  
    2904:	ff                   	(bad)  
    2905:	ff                   	(bad)  
    2906:	ff                   	(bad)  
    2907:	ff                   	(bad)  
    2908:	ff                   	(bad)  
    2909:	ff                   	(bad)  
    290a:	ff                   	(bad)  
    290b:	ff                   	(bad)  
    290c:	ff                   	(bad)  
    290d:	ff                   	(bad)  
    290e:	ff                   	(bad)  
    290f:	ff                   	(bad)  
    2910:	ff                   	(bad)  
    2911:	ff                   	(bad)  
    2912:	ff                   	(bad)  
    2913:	ff                   	(bad)  
    2914:	ff                   	(bad)  
    2915:	ff                   	(bad)  
    2916:	ff                   	(bad)  
    2917:	ff                   	(bad)  
    2918:	ff                   	(bad)  
    2919:	ff                   	(bad)  
    291a:	ff                   	(bad)  
    291b:	ff                   	(bad)  
    291c:	ff                   	(bad)  
    291d:	ff                   	(bad)  
    291e:	ff                   	(bad)  
    291f:	ff                   	(bad)  
    2920:	ff                   	(bad)  
    2921:	ff                   	(bad)  
    2922:	ff                   	(bad)  
    2923:	ff                   	(bad)  
    2924:	ff                   	(bad)  
    2925:	ff                   	(bad)  
    2926:	ff                   	(bad)  
    2927:	ff                   	(bad)  
    2928:	ff                   	(bad)  
    2929:	ff                   	(bad)  
    292a:	ff                   	(bad)  
    292b:	ff                   	(bad)  
    292c:	ff                   	(bad)  
    292d:	ff                   	(bad)  
    292e:	ff                   	(bad)  
    292f:	ff                   	(bad)  
    2930:	ff                   	(bad)  
    2931:	ff                   	(bad)  
    2932:	ff                   	(bad)  
    2933:	ff                   	(bad)  
    2934:	ff                   	(bad)  
    2935:	ff                   	(bad)  
    2936:	ff                   	(bad)  
    2937:	ff                   	(bad)  
    2938:	ff                   	(bad)  
    2939:	ff                   	(bad)  
    293a:	ff                   	(bad)  
    293b:	ff                   	(bad)  
    293c:	ff                   	(bad)  
    293d:	ff                   	(bad)  
    293e:	ff                   	(bad)  
    293f:	ff                   	(bad)  
    2940:	ff                   	(bad)  
    2941:	ff                   	(bad)  
    2942:	ff                   	(bad)  
    2943:	ff                   	(bad)  
    2944:	ff                   	(bad)  
    2945:	ff                   	(bad)  
    2946:	ff                   	(bad)  
    2947:	ff                   	(bad)  
    2948:	ff                   	(bad)  
    2949:	ff                   	(bad)  
    294a:	ff                   	(bad)  
    294b:	ff                   	(bad)  
    294c:	ff                   	(bad)  
    294d:	ff                   	(bad)  
    294e:	ff                   	(bad)  
    294f:	ff                   	(bad)  
    2950:	ff                   	(bad)  
    2951:	ff                   	(bad)  
    2952:	ff                   	(bad)  
    2953:	ff                   	(bad)  
    2954:	ff                   	(bad)  
    2955:	ff                   	(bad)  
    2956:	ff                   	(bad)  
    2957:	ff                   	(bad)  
    2958:	ff                   	(bad)  
    2959:	ff                   	(bad)  
    295a:	ff                   	(bad)  
    295b:	ff                   	(bad)  
    295c:	ff                   	(bad)  
    295d:	ff                   	(bad)  
    295e:	ff                   	(bad)  
    295f:	ff                   	(bad)  
    2960:	ff                   	(bad)  
    2961:	ff                   	(bad)  
    2962:	ff                   	(bad)  
    2963:	ff                   	(bad)  
    2964:	ff                   	(bad)  
    2965:	ff                   	(bad)  
    2966:	ff                   	(bad)  
    2967:	ff                   	(bad)  
    2968:	ff                   	(bad)  
    2969:	ff                   	(bad)  
    296a:	ff                   	(bad)  
    296b:	ff                   	(bad)  
    296c:	ff                   	(bad)  
    296d:	ff                   	(bad)  
    296e:	ff                   	(bad)  
    296f:	ff                   	(bad)  
    2970:	ff                   	(bad)  
    2971:	ff                   	(bad)  
    2972:	ff                   	(bad)  
    2973:	ff                   	(bad)  
    2974:	ff                   	(bad)  
    2975:	ff                   	(bad)  
    2976:	ff                   	(bad)  
    2977:	ff                   	(bad)  
    2978:	ff                   	(bad)  
    2979:	ff                   	(bad)  
    297a:	ff                   	(bad)  
    297b:	ff                   	(bad)  
    297c:	ff                   	(bad)  
    297d:	ff                   	(bad)  
    297e:	ff                   	(bad)  
    297f:	ff                   	(bad)  
    2980:	ff                   	(bad)  
    2981:	ff                   	(bad)  
    2982:	ff                   	(bad)  
    2983:	ff                   	(bad)  
    2984:	ff                   	(bad)  
    2985:	ff                   	(bad)  
    2986:	ff                   	(bad)  
    2987:	ff                   	(bad)  
    2988:	ff                   	(bad)  
    2989:	ff                   	(bad)  
    298a:	ff                   	(bad)  
    298b:	ff                   	(bad)  
    298c:	ff                   	(bad)  
    298d:	ff                   	(bad)  
    298e:	ff                   	(bad)  
    298f:	ff                   	(bad)  
    2990:	ff                   	(bad)  
    2991:	ff                   	(bad)  
    2992:	ff                   	(bad)  
    2993:	ff                   	(bad)  
    2994:	ff                   	(bad)  
    2995:	ff                   	(bad)  
    2996:	ff                   	(bad)  
    2997:	ff                   	(bad)  
    2998:	ff                   	(bad)  
    2999:	ff                   	(bad)  
    299a:	ff                   	(bad)  
    299b:	ff                   	(bad)  
    299c:	ff                   	(bad)  
    299d:	ff                   	(bad)  
    299e:	ff                   	(bad)  
    299f:	ff                   	(bad)  
    29a0:	ff                   	(bad)  
    29a1:	ff                   	(bad)  
    29a2:	ff                   	(bad)  
    29a3:	ff                   	(bad)  
    29a4:	ff                   	(bad)  
    29a5:	ff                   	(bad)  
    29a6:	ff                   	(bad)  
    29a7:	ff                   	(bad)  
    29a8:	ff                   	(bad)  
    29a9:	ff                   	(bad)  
    29aa:	ff                   	(bad)  
    29ab:	ff                   	(bad)  
    29ac:	ff                   	(bad)  
    29ad:	ff                   	(bad)  
    29ae:	ff                   	(bad)  
    29af:	ff                   	(bad)  
    29b0:	ff                   	(bad)  
    29b1:	ff                   	(bad)  
    29b2:	ff                   	(bad)  
    29b3:	ff                   	(bad)  
    29b4:	ff                   	(bad)  
    29b5:	ff                   	(bad)  
    29b6:	ff                   	(bad)  
    29b7:	ff                   	(bad)  
    29b8:	ff                   	(bad)  
    29b9:	ff                   	(bad)  
    29ba:	ff                   	(bad)  
    29bb:	ff                   	(bad)  
    29bc:	ff                   	(bad)  
    29bd:	ff                   	(bad)  
    29be:	ff                   	(bad)  
    29bf:	ff                   	(bad)  
    29c0:	ff                   	(bad)  
    29c1:	ff                   	(bad)  
    29c2:	ff                   	(bad)  
    29c3:	ff                   	(bad)  
    29c4:	ff                   	(bad)  
    29c5:	ff                   	(bad)  
    29c6:	ff                   	(bad)  
    29c7:	ff                   	(bad)  
    29c8:	ff                   	(bad)  
    29c9:	ff                   	(bad)  
    29ca:	ff                   	(bad)  
    29cb:	ff                   	(bad)  
    29cc:	ff                   	(bad)  
    29cd:	ff                   	(bad)  
    29ce:	ff                   	(bad)  
    29cf:	ff                   	(bad)  
    29d0:	ff                   	(bad)  
    29d1:	ff                   	(bad)  
    29d2:	ff                   	(bad)  
    29d3:	ff                   	(bad)  
    29d4:	ff                   	(bad)  
    29d5:	ff                   	(bad)  
    29d6:	ff                   	(bad)  
    29d7:	ff                   	(bad)  
    29d8:	ff                   	(bad)  
    29d9:	ff                   	(bad)  
    29da:	ff                   	(bad)  
    29db:	ff                   	(bad)  
    29dc:	ff                   	(bad)  
    29dd:	ff                   	(bad)  
    29de:	ff                   	(bad)  
    29df:	ff                   	(bad)  
    29e0:	ff                   	(bad)  
    29e1:	ff                   	(bad)  
    29e2:	ff                   	(bad)  
    29e3:	ff                   	(bad)  
    29e4:	ff                   	(bad)  
    29e5:	ff                   	(bad)  
    29e6:	ff                   	(bad)  
    29e7:	ff                   	(bad)  
    29e8:	ff                   	(bad)  
    29e9:	ff                   	(bad)  
    29ea:	ff                   	(bad)  
    29eb:	ff                   	(bad)  
    29ec:	ff                   	(bad)  
    29ed:	ff                   	(bad)  
    29ee:	ff                   	(bad)  
    29ef:	ff                   	(bad)  
    29f0:	ff                   	(bad)  
    29f1:	ff                   	(bad)  
    29f2:	ff                   	(bad)  
    29f3:	ff                   	(bad)  
    29f4:	ff                   	(bad)  
    29f5:	ff                   	(bad)  
    29f6:	ff                   	(bad)  
    29f7:	ff                   	(bad)  
    29f8:	ff                   	(bad)  
    29f9:	ff                   	(bad)  
    29fa:	ff                   	(bad)  
    29fb:	ff                   	(bad)  
    29fc:	ff                   	(bad)  
    29fd:	ff                   	(bad)  
    29fe:	ff                   	(bad)  
    29ff:	ff                   	(bad)  
    2a00:	ff                   	(bad)  
    2a01:	ff                   	(bad)  
    2a02:	ff                   	(bad)  
    2a03:	ff                   	(bad)  
    2a04:	ff                   	(bad)  
    2a05:	ff                   	(bad)  
    2a06:	ff                   	(bad)  
    2a07:	ff                   	(bad)  
    2a08:	ff                   	(bad)  
    2a09:	ff                   	(bad)  
    2a0a:	ff                   	(bad)  
    2a0b:	ff                   	(bad)  
    2a0c:	ff                   	(bad)  
    2a0d:	ff                   	(bad)  
    2a0e:	ff                   	(bad)  
    2a0f:	ff                   	(bad)  
    2a10:	ff                   	(bad)  
    2a11:	ff                   	(bad)  
    2a12:	ff                   	(bad)  
    2a13:	ff                   	(bad)  
    2a14:	ff                   	(bad)  
    2a15:	ff                   	(bad)  
    2a16:	ff                   	(bad)  
    2a17:	ff                   	(bad)  
    2a18:	ff                   	(bad)  
    2a19:	ff                   	(bad)  
    2a1a:	ff                   	(bad)  
    2a1b:	ff                   	(bad)  
    2a1c:	ff                   	(bad)  
    2a1d:	ff                   	(bad)  
    2a1e:	ff                   	(bad)  
    2a1f:	ff                   	(bad)  
    2a20:	ff                   	(bad)  
    2a21:	ff                   	(bad)  
    2a22:	ff                   	(bad)  
    2a23:	ff                   	(bad)  
    2a24:	ff                   	(bad)  
    2a25:	ff                   	(bad)  
    2a26:	ff                   	(bad)  
    2a27:	ff                   	(bad)  
    2a28:	ff                   	(bad)  
    2a29:	ff                   	(bad)  
    2a2a:	ff                   	(bad)  
    2a2b:	ff                   	(bad)  
    2a2c:	ff                   	(bad)  
    2a2d:	ff                   	(bad)  
    2a2e:	ff                   	(bad)  
    2a2f:	ff                   	(bad)  
    2a30:	ff                   	(bad)  
    2a31:	ff                   	(bad)  
    2a32:	ff                   	(bad)  
    2a33:	ff                   	(bad)  
    2a34:	ff                   	(bad)  
    2a35:	ff                   	(bad)  
    2a36:	ff                   	(bad)  
    2a37:	ff                   	(bad)  
    2a38:	ff                   	(bad)  
    2a39:	ff                   	(bad)  
    2a3a:	ff                   	(bad)  
    2a3b:	ff                   	(bad)  
    2a3c:	ff                   	(bad)  
    2a3d:	ff                   	(bad)  
    2a3e:	ff                   	(bad)  
    2a3f:	ff                   	(bad)  
    2a40:	ff                   	(bad)  
    2a41:	ff                   	(bad)  
    2a42:	ff                   	(bad)  
    2a43:	ff                   	(bad)  
    2a44:	ff                   	(bad)  
    2a45:	ff                   	(bad)  
    2a46:	ff                   	(bad)  
    2a47:	ff                   	(bad)  
    2a48:	ff                   	(bad)  
    2a49:	ff                   	(bad)  
    2a4a:	ff                   	(bad)  
    2a4b:	ff                   	(bad)  
    2a4c:	ff                   	(bad)  
    2a4d:	ff                   	(bad)  
    2a4e:	ff                   	(bad)  
    2a4f:	ff                   	(bad)  
    2a50:	ff                   	(bad)  
    2a51:	ff                   	(bad)  
    2a52:	ff                   	(bad)  
    2a53:	ff                   	(bad)  
    2a54:	ff                   	(bad)  
    2a55:	ff                   	(bad)  
    2a56:	ff                   	(bad)  
    2a57:	ff                   	(bad)  
    2a58:	ff                   	(bad)  
    2a59:	ff                   	(bad)  
    2a5a:	ff                   	(bad)  
    2a5b:	ff                   	(bad)  
    2a5c:	ff                   	(bad)  
    2a5d:	ff                   	(bad)  
    2a5e:	ff                   	(bad)  
    2a5f:	ff                   	(bad)  
    2a60:	ff                   	(bad)  
    2a61:	ff                   	(bad)  
    2a62:	ff                   	(bad)  
    2a63:	ff                   	(bad)  
    2a64:	ff                   	(bad)  
    2a65:	ff                   	(bad)  
    2a66:	ff                   	(bad)  
    2a67:	ff                   	(bad)  
    2a68:	ff                   	(bad)  
    2a69:	ff                   	(bad)  
    2a6a:	ff                   	(bad)  
    2a6b:	ff                   	(bad)  
    2a6c:	ff                   	(bad)  
    2a6d:	ff                   	(bad)  
    2a6e:	ff                   	(bad)  
    2a6f:	ff                   	(bad)  
    2a70:	ff                   	(bad)  
    2a71:	ff                   	(bad)  
    2a72:	ff                   	(bad)  
    2a73:	ff                   	(bad)  
    2a74:	ff                   	(bad)  
    2a75:	ff                   	(bad)  
    2a76:	ff                   	(bad)  
    2a77:	ff                   	(bad)  
    2a78:	ff                   	(bad)  
    2a79:	ff                   	(bad)  
    2a7a:	ff                   	(bad)  
    2a7b:	ff                   	(bad)  
    2a7c:	ff                   	(bad)  
    2a7d:	ff                   	(bad)  
    2a7e:	ff                   	(bad)  
    2a7f:	ff                   	(bad)  
    2a80:	ff                   	(bad)  
    2a81:	ff                   	(bad)  
    2a82:	ff                   	(bad)  
    2a83:	ff                   	(bad)  
    2a84:	ff                   	(bad)  
    2a85:	ff                   	(bad)  
    2a86:	ff                   	(bad)  
    2a87:	ff                   	(bad)  
    2a88:	ff                   	(bad)  
    2a89:	ff                   	(bad)  
    2a8a:	ff                   	(bad)  
    2a8b:	ff                   	(bad)  
    2a8c:	ff                   	(bad)  
    2a8d:	ff                   	(bad)  
    2a8e:	ff                   	(bad)  
    2a8f:	ff                   	(bad)  
    2a90:	ff                   	(bad)  
    2a91:	ff                   	(bad)  
    2a92:	ff                   	(bad)  
    2a93:	ff                   	(bad)  
    2a94:	ff                   	(bad)  
    2a95:	ff                   	(bad)  
    2a96:	ff                   	(bad)  
    2a97:	ff                   	(bad)  
    2a98:	ff                   	(bad)  
    2a99:	ff                   	(bad)  
    2a9a:	ff                   	(bad)  
    2a9b:	ff                   	(bad)  
    2a9c:	ff                   	(bad)  
    2a9d:	ff                   	(bad)  
    2a9e:	ff                   	(bad)  
    2a9f:	ff                   	(bad)  
    2aa0:	ff                   	(bad)  
    2aa1:	ff                   	(bad)  
    2aa2:	ff                   	(bad)  
    2aa3:	ff                   	(bad)  
    2aa4:	ff                   	(bad)  
    2aa5:	ff                   	(bad)  
    2aa6:	ff                   	(bad)  
    2aa7:	ff                   	(bad)  
    2aa8:	ff                   	(bad)  
    2aa9:	ff                   	(bad)  
    2aaa:	ff                   	(bad)  
    2aab:	ff                   	(bad)  
    2aac:	ff                   	(bad)  
    2aad:	ff                   	(bad)  
    2aae:	ff                   	(bad)  
    2aaf:	ff                   	(bad)  
    2ab0:	ff                   	(bad)  
    2ab1:	ff                   	(bad)  
    2ab2:	ff                   	(bad)  
    2ab3:	ff                   	(bad)  
    2ab4:	ff                   	(bad)  
    2ab5:	ff                   	(bad)  
    2ab6:	ff                   	(bad)  
    2ab7:	ff                   	(bad)  
    2ab8:	ff                   	(bad)  
    2ab9:	ff                   	(bad)  
    2aba:	ff                   	(bad)  
    2abb:	ff                   	(bad)  
    2abc:	ff                   	(bad)  
    2abd:	ff                   	(bad)  
    2abe:	ff                   	(bad)  
    2abf:	ff                   	(bad)  
    2ac0:	ff                   	(bad)  
    2ac1:	ff                   	(bad)  
    2ac2:	ff                   	(bad)  
    2ac3:	ff                   	(bad)  
    2ac4:	ff                   	(bad)  
    2ac5:	ff                   	(bad)  
    2ac6:	ff                   	(bad)  
    2ac7:	ff                   	(bad)  
    2ac8:	ff                   	(bad)  
    2ac9:	ff                   	(bad)  
    2aca:	ff                   	(bad)  
    2acb:	ff                   	(bad)  
    2acc:	ff                   	(bad)  
    2acd:	ff                   	(bad)  
    2ace:	ff                   	(bad)  
    2acf:	ff                   	(bad)  
    2ad0:	ff                   	(bad)  
    2ad1:	ff                   	(bad)  
    2ad2:	ff                   	(bad)  
    2ad3:	ff                   	(bad)  
    2ad4:	ff                   	(bad)  
    2ad5:	ff                   	(bad)  
    2ad6:	ff                   	(bad)  
    2ad7:	ff                   	(bad)  
    2ad8:	ff                   	(bad)  
    2ad9:	ff                   	(bad)  
    2ada:	ff                   	(bad)  
    2adb:	ff                   	(bad)  
    2adc:	ff                   	(bad)  
    2add:	ff                   	(bad)  
    2ade:	ff                   	(bad)  
    2adf:	ff                   	(bad)  
    2ae0:	ff                   	(bad)  
    2ae1:	ff                   	(bad)  
    2ae2:	ff                   	(bad)  
    2ae3:	ff                   	(bad)  
    2ae4:	ff                   	(bad)  
    2ae5:	ff                   	(bad)  
    2ae6:	ff                   	(bad)  
    2ae7:	ff                   	(bad)  
    2ae8:	ff                   	(bad)  
    2ae9:	ff                   	(bad)  
    2aea:	ff                   	(bad)  
    2aeb:	ff                   	(bad)  
    2aec:	ff                   	(bad)  
    2aed:	ff                   	(bad)  
    2aee:	ff                   	(bad)  
    2aef:	ff                   	(bad)  
    2af0:	ff                   	(bad)  
    2af1:	ff                   	(bad)  
    2af2:	ff                   	(bad)  
    2af3:	ff                   	(bad)  
    2af4:	ff                   	(bad)  
    2af5:	ff                   	(bad)  
    2af6:	ff                   	(bad)  
    2af7:	ff                   	(bad)  
    2af8:	ff                   	(bad)  
    2af9:	ff                   	(bad)  
    2afa:	ff                   	(bad)  
    2afb:	ff                   	(bad)  
    2afc:	ff                   	(bad)  
    2afd:	ff                   	(bad)  
    2afe:	ff                   	(bad)  
    2aff:	ff                   	(bad)  
    2b00:	ff                   	(bad)  
    2b01:	ff                   	(bad)  
    2b02:	ff                   	(bad)  
    2b03:	ff                   	(bad)  
    2b04:	ff                   	(bad)  
    2b05:	ff                   	(bad)  
    2b06:	ff                   	(bad)  
    2b07:	ff                   	(bad)  
    2b08:	ff                   	(bad)  
    2b09:	ff                   	(bad)  
    2b0a:	ff                   	(bad)  
    2b0b:	ff                   	(bad)  
    2b0c:	ff                   	(bad)  
    2b0d:	ff                   	(bad)  
    2b0e:	ff                   	(bad)  
    2b0f:	ff                   	(bad)  
    2b10:	ff                   	(bad)  
    2b11:	ff                   	(bad)  
    2b12:	ff                   	(bad)  
    2b13:	ff                   	(bad)  
    2b14:	ff                   	(bad)  
    2b15:	ff                   	(bad)  
    2b16:	ff                   	(bad)  
    2b17:	ff                   	(bad)  
    2b18:	ff                   	(bad)  
    2b19:	ff                   	(bad)  
    2b1a:	ff                   	(bad)  
    2b1b:	ff                   	(bad)  
    2b1c:	ff                   	(bad)  
    2b1d:	ff                   	(bad)  
    2b1e:	ff                   	(bad)  
    2b1f:	ff                   	(bad)  
    2b20:	ff                   	(bad)  
    2b21:	ff                   	(bad)  
    2b22:	ff                   	(bad)  
    2b23:	ff                   	(bad)  
    2b24:	ff                   	(bad)  
    2b25:	ff                   	(bad)  
    2b26:	ff                   	(bad)  
    2b27:	ff                   	(bad)  
    2b28:	ff                   	(bad)  
    2b29:	ff                   	(bad)  
    2b2a:	ff                   	(bad)  
    2b2b:	ff                   	(bad)  
    2b2c:	ff                   	(bad)  
    2b2d:	ff                   	(bad)  
    2b2e:	ff                   	(bad)  
    2b2f:	ff                   	(bad)  
    2b30:	ff                   	(bad)  
    2b31:	ff                   	(bad)  
    2b32:	ff                   	(bad)  
    2b33:	ff                   	(bad)  
    2b34:	ff                   	(bad)  
    2b35:	ff                   	(bad)  
    2b36:	ff                   	(bad)  
    2b37:	ff                   	(bad)  
    2b38:	ff                   	(bad)  
    2b39:	ff                   	(bad)  
    2b3a:	ff                   	(bad)  
    2b3b:	ff                   	(bad)  
    2b3c:	ff                   	(bad)  
    2b3d:	ff                   	(bad)  
    2b3e:	ff                   	(bad)  
    2b3f:	ff                   	(bad)  
    2b40:	ff                   	(bad)  
    2b41:	ff                   	(bad)  
    2b42:	ff                   	(bad)  
    2b43:	ff                   	(bad)  
    2b44:	ff                   	(bad)  
    2b45:	ff                   	(bad)  
    2b46:	ff                   	(bad)  
    2b47:	ff                   	(bad)  
    2b48:	ff                   	(bad)  
    2b49:	ff                   	(bad)  
    2b4a:	ff                   	(bad)  
    2b4b:	ff                   	(bad)  
    2b4c:	ff                   	(bad)  
    2b4d:	ff                   	(bad)  
    2b4e:	ff                   	(bad)  
    2b4f:	ff                   	(bad)  
    2b50:	ff                   	(bad)  
    2b51:	ff                   	(bad)  
    2b52:	ff                   	(bad)  
    2b53:	ff                   	(bad)  
    2b54:	ff                   	(bad)  
    2b55:	ff                   	(bad)  
    2b56:	ff                   	(bad)  
    2b57:	ff                   	(bad)  
    2b58:	ff                   	(bad)  
    2b59:	ff                   	(bad)  
    2b5a:	ff                   	(bad)  
    2b5b:	ff                   	(bad)  
    2b5c:	ff                   	(bad)  
    2b5d:	ff                   	(bad)  
    2b5e:	ff                   	(bad)  
    2b5f:	ff                   	(bad)  
    2b60:	ff                   	(bad)  
    2b61:	ff                   	(bad)  
    2b62:	ff                   	(bad)  
    2b63:	ff                   	(bad)  
    2b64:	ff                   	(bad)  
    2b65:	ff                   	(bad)  
    2b66:	ff                   	(bad)  
    2b67:	ff                   	(bad)  
    2b68:	ff                   	(bad)  
    2b69:	ff                   	(bad)  
    2b6a:	ff                   	(bad)  
    2b6b:	ff                   	(bad)  
    2b6c:	ff                   	(bad)  
    2b6d:	ff                   	(bad)  
    2b6e:	ff                   	(bad)  
    2b6f:	ff                   	(bad)  
    2b70:	ff                   	(bad)  
    2b71:	ff                   	(bad)  
    2b72:	ff                   	(bad)  
    2b73:	ff                   	(bad)  
    2b74:	ff                   	(bad)  
    2b75:	ff                   	(bad)  
    2b76:	ff                   	(bad)  
    2b77:	ff                   	(bad)  
    2b78:	ff                   	(bad)  
    2b79:	ff                   	(bad)  
    2b7a:	ff                   	(bad)  
    2b7b:	ff                   	(bad)  
    2b7c:	ff                   	(bad)  
    2b7d:	ff                   	(bad)  
    2b7e:	ff                   	(bad)  
    2b7f:	ff                   	(bad)  
    2b80:	ff                   	(bad)  
    2b81:	ff                   	(bad)  
    2b82:	ff                   	(bad)  
    2b83:	ff                   	(bad)  
    2b84:	ff                   	(bad)  
    2b85:	ff                   	(bad)  
    2b86:	ff                   	(bad)  
    2b87:	ff                   	(bad)  
    2b88:	ff                   	(bad)  
    2b89:	ff                   	(bad)  
    2b8a:	ff                   	(bad)  
    2b8b:	ff                   	(bad)  
    2b8c:	ff                   	(bad)  
    2b8d:	ff                   	(bad)  
    2b8e:	ff                   	(bad)  
    2b8f:	ff                   	(bad)  
    2b90:	ff                   	(bad)  
    2b91:	ff                   	(bad)  
    2b92:	ff                   	(bad)  
    2b93:	ff                   	(bad)  
    2b94:	ff                   	(bad)  
    2b95:	ff                   	(bad)  
    2b96:	ff                   	(bad)  
    2b97:	ff                   	(bad)  
    2b98:	ff                   	(bad)  
    2b99:	ff                   	(bad)  
    2b9a:	ff                   	(bad)  
    2b9b:	ff                   	(bad)  
    2b9c:	ff                   	(bad)  
    2b9d:	ff                   	(bad)  
    2b9e:	ff                   	(bad)  
    2b9f:	ff                   	(bad)  
    2ba0:	ff                   	(bad)  
    2ba1:	ff                   	(bad)  
    2ba2:	ff                   	(bad)  
    2ba3:	ff                   	(bad)  
    2ba4:	ff                   	(bad)  
    2ba5:	ff                   	(bad)  
    2ba6:	ff                   	(bad)  
    2ba7:	ff                   	(bad)  
    2ba8:	ff                   	(bad)  
    2ba9:	ff                   	(bad)  
    2baa:	ff                   	(bad)  
    2bab:	ff                   	(bad)  
    2bac:	ff                   	(bad)  
    2bad:	ff                   	(bad)  
    2bae:	ff                   	(bad)  
    2baf:	ff                   	(bad)  
    2bb0:	ff                   	(bad)  
    2bb1:	ff                   	(bad)  
    2bb2:	ff                   	(bad)  
    2bb3:	ff                   	(bad)  
    2bb4:	ff                   	(bad)  
    2bb5:	ff                   	(bad)  
    2bb6:	ff                   	(bad)  
    2bb7:	ff                   	(bad)  
    2bb8:	ff                   	(bad)  
    2bb9:	ff                   	(bad)  
    2bba:	ff                   	(bad)  
    2bbb:	ff                   	(bad)  
    2bbc:	ff                   	(bad)  
    2bbd:	ff                   	(bad)  
    2bbe:	ff                   	(bad)  
    2bbf:	ff                   	(bad)  
    2bc0:	ff                   	(bad)  
    2bc1:	ff                   	(bad)  
    2bc2:	ff                   	(bad)  
    2bc3:	ff                   	(bad)  
    2bc4:	ff                   	(bad)  
    2bc5:	ff                   	(bad)  
    2bc6:	ff                   	(bad)  
    2bc7:	ff                   	(bad)  
    2bc8:	ff                   	(bad)  
    2bc9:	ff                   	(bad)  
    2bca:	ff                   	(bad)  
    2bcb:	ff                   	(bad)  
    2bcc:	ff                   	(bad)  
    2bcd:	ff                   	(bad)  
    2bce:	ff                   	(bad)  
    2bcf:	ff                   	(bad)  
    2bd0:	ff                   	(bad)  
    2bd1:	ff                   	(bad)  
    2bd2:	ff                   	(bad)  
    2bd3:	ff                   	(bad)  
    2bd4:	ff                   	(bad)  
    2bd5:	ff                   	(bad)  
    2bd6:	ff                   	(bad)  
    2bd7:	ff                   	(bad)  
    2bd8:	ff                   	(bad)  
    2bd9:	ff                   	(bad)  
    2bda:	ff                   	(bad)  
    2bdb:	ff                   	(bad)  
    2bdc:	ff                   	(bad)  
    2bdd:	ff                   	(bad)  
    2bde:	ff                   	(bad)  
    2bdf:	ff                   	(bad)  
    2be0:	ff                   	(bad)  
    2be1:	ff                   	(bad)  
    2be2:	ff                   	(bad)  
    2be3:	ff                   	(bad)  
    2be4:	ff                   	(bad)  
    2be5:	ff                   	(bad)  
    2be6:	ff                   	(bad)  
    2be7:	ff                   	(bad)  
    2be8:	ff                   	(bad)  
    2be9:	ff                   	(bad)  
    2bea:	ff                   	(bad)  
    2beb:	ff                   	(bad)  
    2bec:	ff                   	(bad)  
    2bed:	ff                   	(bad)  
    2bee:	ff                   	(bad)  
    2bef:	ff                   	(bad)  
    2bf0:	ff                   	(bad)  
    2bf1:	ff                   	(bad)  
    2bf2:	ff                   	(bad)  
    2bf3:	ff                   	(bad)  
    2bf4:	ff                   	(bad)  
    2bf5:	ff                   	(bad)  
    2bf6:	ff                   	(bad)  
    2bf7:	ff                   	(bad)  
    2bf8:	ff                   	(bad)  
    2bf9:	ff                   	(bad)  
    2bfa:	ff                   	(bad)  
    2bfb:	ff                   	(bad)  
    2bfc:	ff                   	(bad)  
    2bfd:	ff                   	(bad)  
    2bfe:	ff                   	(bad)  
    2bff:	ff                   	(bad)  
    2c00:	ff                   	(bad)  
    2c01:	ff                   	(bad)  
    2c02:	ff                   	(bad)  
    2c03:	ff                   	(bad)  
    2c04:	ff                   	(bad)  
    2c05:	ff                   	(bad)  
    2c06:	ff                   	(bad)  
    2c07:	ff                   	(bad)  
    2c08:	ff                   	(bad)  
    2c09:	ff                   	(bad)  
    2c0a:	ff                   	(bad)  
    2c0b:	ff                   	(bad)  
    2c0c:	ff                   	(bad)  
    2c0d:	ff                   	(bad)  
    2c0e:	ff                   	(bad)  
    2c0f:	ff                   	(bad)  
    2c10:	ff                   	(bad)  
    2c11:	ff                   	(bad)  
    2c12:	ff                   	(bad)  
    2c13:	ff                   	(bad)  
    2c14:	ff                   	(bad)  
    2c15:	ff                   	(bad)  
    2c16:	ff                   	(bad)  
    2c17:	ff                   	(bad)  
    2c18:	ff                   	(bad)  
    2c19:	ff                   	(bad)  
    2c1a:	ff                   	(bad)  
    2c1b:	ff                   	(bad)  
    2c1c:	ff                   	(bad)  
    2c1d:	ff                   	(bad)  
    2c1e:	ff                   	(bad)  
    2c1f:	ff                   	(bad)  
    2c20:	ff                   	(bad)  
    2c21:	ff                   	(bad)  
    2c22:	ff                   	(bad)  
    2c23:	ff                   	(bad)  
    2c24:	ff                   	(bad)  
    2c25:	ff                   	(bad)  
    2c26:	ff                   	(bad)  
    2c27:	ff                   	(bad)  
    2c28:	ff                   	(bad)  
    2c29:	ff                   	(bad)  
    2c2a:	ff                   	(bad)  
    2c2b:	ff                   	(bad)  
    2c2c:	ff                   	(bad)  
    2c2d:	ff                   	(bad)  
    2c2e:	ff                   	(bad)  
    2c2f:	ff                   	(bad)  
    2c30:	ff                   	(bad)  
    2c31:	ff                   	(bad)  
    2c32:	ff                   	(bad)  
    2c33:	ff                   	(bad)  
    2c34:	ff                   	(bad)  
    2c35:	ff                   	(bad)  
    2c36:	ff                   	(bad)  
    2c37:	ff                   	(bad)  
    2c38:	ff                   	(bad)  
    2c39:	ff                   	(bad)  
    2c3a:	ff                   	(bad)  
    2c3b:	ff                   	(bad)  
    2c3c:	ff                   	(bad)  
    2c3d:	ff                   	(bad)  
    2c3e:	ff                   	(bad)  
    2c3f:	ff                   	(bad)  
    2c40:	ff                   	(bad)  
    2c41:	ff                   	(bad)  
    2c42:	ff                   	(bad)  
    2c43:	ff                   	(bad)  
    2c44:	ff                   	(bad)  
    2c45:	ff                   	(bad)  
    2c46:	ff                   	(bad)  
    2c47:	ff                   	(bad)  
    2c48:	ff                   	(bad)  
    2c49:	ff                   	(bad)  
    2c4a:	ff                   	(bad)  
    2c4b:	ff                   	(bad)  
    2c4c:	ff                   	(bad)  
    2c4d:	ff                   	(bad)  
    2c4e:	ff                   	(bad)  
    2c4f:	ff                   	(bad)  
    2c50:	ff                   	(bad)  
    2c51:	ff                   	(bad)  
    2c52:	ff                   	(bad)  
    2c53:	ff                   	(bad)  
    2c54:	ff                   	(bad)  
    2c55:	ff                   	(bad)  
    2c56:	ff                   	(bad)  
    2c57:	ff                   	(bad)  
    2c58:	ff                   	(bad)  
    2c59:	ff                   	(bad)  
    2c5a:	ff                   	(bad)  
    2c5b:	ff                   	(bad)  
    2c5c:	ff                   	(bad)  
    2c5d:	ff                   	(bad)  
    2c5e:	ff                   	(bad)  
    2c5f:	ff                   	(bad)  
    2c60:	ff                   	(bad)  
    2c61:	ff                   	(bad)  
    2c62:	ff                   	(bad)  
    2c63:	ff                   	(bad)  
    2c64:	ff                   	(bad)  
    2c65:	ff                   	(bad)  
    2c66:	ff                   	(bad)  
    2c67:	ff                   	(bad)  
    2c68:	ff                   	(bad)  
    2c69:	ff                   	(bad)  
    2c6a:	ff                   	(bad)  
    2c6b:	ff                   	(bad)  
    2c6c:	ff                   	(bad)  
    2c6d:	ff                   	(bad)  
    2c6e:	ff                   	(bad)  
    2c6f:	ff                   	(bad)  
    2c70:	ff                   	(bad)  
    2c71:	ff                   	(bad)  
    2c72:	ff                   	(bad)  
    2c73:	ff                   	(bad)  
    2c74:	ff                   	(bad)  
    2c75:	ff                   	(bad)  
    2c76:	ff                   	(bad)  
    2c77:	ff                   	(bad)  
    2c78:	ff                   	(bad)  
    2c79:	ff                   	(bad)  
    2c7a:	ff                   	(bad)  
    2c7b:	ff                   	(bad)  
    2c7c:	ff                   	(bad)  
    2c7d:	ff                   	(bad)  
    2c7e:	ff                   	(bad)  
    2c7f:	ff                   	(bad)  
    2c80:	ff                   	(bad)  
    2c81:	ff                   	(bad)  
    2c82:	ff                   	(bad)  
    2c83:	ff                   	(bad)  
    2c84:	ff                   	(bad)  
    2c85:	ff                   	(bad)  
    2c86:	ff                   	(bad)  
    2c87:	ff                   	(bad)  
    2c88:	ff                   	(bad)  
    2c89:	ff                   	(bad)  
    2c8a:	ff                   	(bad)  
    2c8b:	ff                   	(bad)  
    2c8c:	ff                   	(bad)  
    2c8d:	ff                   	(bad)  
    2c8e:	ff                   	(bad)  
    2c8f:	ff                   	(bad)  
    2c90:	ff                   	(bad)  
    2c91:	ff                   	(bad)  
    2c92:	ff                   	(bad)  
    2c93:	ff                   	(bad)  
    2c94:	ff                   	(bad)  
    2c95:	ff                   	(bad)  
    2c96:	ff                   	(bad)  
    2c97:	ff                   	(bad)  
    2c98:	ff                   	(bad)  
    2c99:	ff                   	(bad)  
    2c9a:	ff                   	(bad)  
    2c9b:	ff                   	(bad)  
    2c9c:	ff                   	(bad)  
    2c9d:	ff                   	(bad)  
    2c9e:	ff                   	(bad)  
    2c9f:	ff                   	(bad)  
    2ca0:	ff                   	(bad)  
    2ca1:	ff                   	(bad)  
    2ca2:	ff                   	(bad)  
    2ca3:	ff                   	(bad)  
    2ca4:	ff                   	(bad)  
    2ca5:	ff                   	(bad)  
    2ca6:	ff                   	(bad)  
    2ca7:	ff                   	(bad)  
    2ca8:	ff                   	(bad)  
    2ca9:	ff                   	(bad)  
    2caa:	ff                   	(bad)  
    2cab:	ff                   	(bad)  
    2cac:	ff                   	(bad)  
    2cad:	ff                   	(bad)  
    2cae:	ff                   	(bad)  
    2caf:	ff                   	(bad)  
    2cb0:	ff                   	(bad)  
    2cb1:	ff                   	(bad)  
    2cb2:	ff                   	(bad)  
    2cb3:	ff                   	(bad)  
    2cb4:	ff                   	(bad)  
    2cb5:	ff                   	(bad)  
    2cb6:	ff                   	(bad)  
    2cb7:	ff                   	(bad)  
    2cb8:	ff                   	(bad)  
    2cb9:	ff                   	(bad)  
    2cba:	ff                   	(bad)  
    2cbb:	ff                   	(bad)  
    2cbc:	ff                   	(bad)  
    2cbd:	ff                   	(bad)  
    2cbe:	ff                   	(bad)  
    2cbf:	ff                   	(bad)  
    2cc0:	ff                   	(bad)  
    2cc1:	ff                   	(bad)  
    2cc2:	ff                   	(bad)  
    2cc3:	ff                   	(bad)  
    2cc4:	ff                   	(bad)  
    2cc5:	ff                   	(bad)  
    2cc6:	ff                   	(bad)  
    2cc7:	ff                   	(bad)  
    2cc8:	ff                   	(bad)  
    2cc9:	ff                   	(bad)  
    2cca:	ff                   	(bad)  
    2ccb:	ff                   	(bad)  
    2ccc:	ff                   	(bad)  
    2ccd:	ff                   	(bad)  
    2cce:	ff                   	(bad)  
    2ccf:	ff                   	(bad)  
    2cd0:	ff                   	(bad)  
    2cd1:	ff                   	(bad)  
    2cd2:	ff                   	(bad)  
    2cd3:	ff                   	(bad)  
    2cd4:	ff                   	(bad)  
    2cd5:	ff                   	(bad)  
    2cd6:	ff                   	(bad)  
    2cd7:	ff                   	(bad)  
    2cd8:	ff                   	(bad)  
    2cd9:	ff                   	(bad)  
    2cda:	ff                   	(bad)  
    2cdb:	ff                   	(bad)  
    2cdc:	ff                   	(bad)  
    2cdd:	ff                   	(bad)  
    2cde:	ff                   	(bad)  
    2cdf:	ff                   	(bad)  
    2ce0:	ff                   	(bad)  
    2ce1:	ff                   	(bad)  
    2ce2:	ff                   	(bad)  
    2ce3:	ff                   	(bad)  
    2ce4:	ff                   	(bad)  
    2ce5:	ff                   	(bad)  
    2ce6:	ff                   	(bad)  
    2ce7:	ff                   	(bad)  
    2ce8:	ff                   	(bad)  
    2ce9:	ff                   	(bad)  
    2cea:	ff                   	(bad)  
    2ceb:	ff                   	(bad)  
    2cec:	ff                   	(bad)  
    2ced:	ff                   	(bad)  
    2cee:	ff                   	(bad)  
    2cef:	ff                   	(bad)  
    2cf0:	ff                   	(bad)  
    2cf1:	ff                   	(bad)  
    2cf2:	ff                   	(bad)  
    2cf3:	ff                   	(bad)  
    2cf4:	ff                   	(bad)  
    2cf5:	ff                   	(bad)  
    2cf6:	ff                   	(bad)  
    2cf7:	ff                   	(bad)  
    2cf8:	ff                   	(bad)  
    2cf9:	ff                   	(bad)  
    2cfa:	ff                   	(bad)  
    2cfb:	ff                   	(bad)  
    2cfc:	ff                   	(bad)  
    2cfd:	ff                   	(bad)  
    2cfe:	ff                   	(bad)  
    2cff:	ff                   	(bad)  
    2d00:	ff                   	(bad)  
    2d01:	ff                   	(bad)  
    2d02:	ff                   	(bad)  
    2d03:	ff                   	(bad)  
    2d04:	ff                   	(bad)  
    2d05:	ff                   	(bad)  
    2d06:	ff                   	(bad)  
    2d07:	ff                   	(bad)  
    2d08:	ff                   	(bad)  
    2d09:	ff                   	(bad)  
    2d0a:	ff                   	(bad)  
    2d0b:	ff                   	(bad)  
    2d0c:	ff                   	(bad)  
    2d0d:	ff                   	(bad)  
    2d0e:	ff                   	(bad)  
    2d0f:	ff                   	(bad)  
    2d10:	ff                   	(bad)  
    2d11:	ff                   	(bad)  
    2d12:	ff                   	(bad)  
    2d13:	ff                   	(bad)  
    2d14:	ff                   	(bad)  
    2d15:	ff                   	(bad)  
    2d16:	ff                   	(bad)  
    2d17:	ff                   	(bad)  
    2d18:	ff                   	(bad)  
    2d19:	ff                   	(bad)  
    2d1a:	ff                   	(bad)  
    2d1b:	ff                   	(bad)  
    2d1c:	ff                   	(bad)  
    2d1d:	ff                   	(bad)  
    2d1e:	ff                   	(bad)  
    2d1f:	ff                   	(bad)  
    2d20:	ff                   	(bad)  
    2d21:	ff                   	(bad)  
    2d22:	ff                   	(bad)  
    2d23:	ff                   	(bad)  
    2d24:	ff                   	(bad)  
    2d25:	ff                   	(bad)  
    2d26:	ff                   	(bad)  
    2d27:	ff                   	(bad)  
    2d28:	ff                   	(bad)  
    2d29:	ff                   	(bad)  
    2d2a:	ff                   	(bad)  
    2d2b:	ff                   	(bad)  
    2d2c:	ff                   	(bad)  
    2d2d:	ff                   	(bad)  
    2d2e:	ff                   	(bad)  
    2d2f:	ff                   	(bad)  
    2d30:	ff                   	(bad)  
    2d31:	ff                   	(bad)  
    2d32:	ff                   	(bad)  
    2d33:	ff                   	(bad)  
    2d34:	ff                   	(bad)  
    2d35:	ff                   	(bad)  
    2d36:	ff                   	(bad)  
    2d37:	ff                   	(bad)  
    2d38:	ff                   	(bad)  
    2d39:	ff                   	(bad)  
    2d3a:	ff                   	(bad)  
    2d3b:	ff                   	(bad)  
    2d3c:	ff                   	(bad)  
    2d3d:	ff                   	(bad)  
    2d3e:	ff                   	(bad)  
    2d3f:	ff                   	(bad)  
    2d40:	ff                   	(bad)  
    2d41:	ff                   	(bad)  
    2d42:	ff                   	(bad)  
    2d43:	ff                   	(bad)  
    2d44:	ff                   	(bad)  
    2d45:	ff                   	(bad)  
    2d46:	ff                   	(bad)  
    2d47:	ff                   	(bad)  
    2d48:	ff                   	(bad)  
    2d49:	ff                   	(bad)  
    2d4a:	ff                   	(bad)  
    2d4b:	ff                   	(bad)  
    2d4c:	ff                   	(bad)  
    2d4d:	ff                   	(bad)  
    2d4e:	ff                   	(bad)  
    2d4f:	ff                   	(bad)  
    2d50:	ff                   	(bad)  
    2d51:	ff                   	(bad)  
    2d52:	ff                   	(bad)  
    2d53:	ff                   	(bad)  
    2d54:	ff                   	(bad)  
    2d55:	ff                   	(bad)  
    2d56:	ff                   	(bad)  
    2d57:	ff                   	(bad)  
    2d58:	ff                   	(bad)  
    2d59:	ff                   	(bad)  
    2d5a:	ff                   	(bad)  
    2d5b:	ff                   	(bad)  
    2d5c:	ff                   	(bad)  
    2d5d:	ff                   	(bad)  
    2d5e:	ff                   	(bad)  
    2d5f:	ff                   	(bad)  
    2d60:	ff                   	(bad)  
    2d61:	ff                   	(bad)  
    2d62:	ff                   	(bad)  
    2d63:	ff                   	(bad)  
    2d64:	ff                   	(bad)  
    2d65:	ff                   	(bad)  
    2d66:	ff                   	(bad)  
    2d67:	ff                   	(bad)  
    2d68:	ff                   	(bad)  
    2d69:	ff                   	(bad)  
    2d6a:	ff                   	(bad)  
    2d6b:	ff                   	(bad)  
    2d6c:	ff                   	(bad)  
    2d6d:	ff                   	(bad)  
    2d6e:	ff                   	(bad)  
    2d6f:	ff                   	(bad)  
    2d70:	ff                   	(bad)  
    2d71:	ff                   	(bad)  
    2d72:	ff                   	(bad)  
    2d73:	ff                   	(bad)  
    2d74:	ff                   	(bad)  
    2d75:	ff                   	(bad)  
    2d76:	ff                   	(bad)  
    2d77:	ff                   	(bad)  
    2d78:	ff                   	(bad)  
    2d79:	ff                   	(bad)  
    2d7a:	ff                   	(bad)  
    2d7b:	ff                   	(bad)  
    2d7c:	ff                   	(bad)  
    2d7d:	ff                   	(bad)  
    2d7e:	ff                   	(bad)  
    2d7f:	ff                   	(bad)  
    2d80:	ff                   	(bad)  
    2d81:	ff                   	(bad)  
    2d82:	ff                   	(bad)  
    2d83:	ff                   	(bad)  
    2d84:	ff                   	(bad)  
    2d85:	ff                   	(bad)  
    2d86:	ff                   	(bad)  
    2d87:	ff                   	(bad)  
    2d88:	ff                   	(bad)  
    2d89:	ff                   	(bad)  
    2d8a:	ff                   	(bad)  
    2d8b:	ff                   	(bad)  
    2d8c:	ff                   	(bad)  
    2d8d:	ff                   	(bad)  
    2d8e:	ff                   	(bad)  
    2d8f:	ff                   	(bad)  
    2d90:	ff                   	(bad)  
    2d91:	ff                   	(bad)  
    2d92:	ff                   	(bad)  
    2d93:	ff                   	(bad)  
    2d94:	ff                   	(bad)  
    2d95:	ff                   	(bad)  
    2d96:	ff                   	(bad)  
    2d97:	ff                   	(bad)  
    2d98:	ff                   	(bad)  
    2d99:	ff                   	(bad)  
    2d9a:	ff                   	(bad)  
    2d9b:	ff                   	(bad)  
    2d9c:	ff                   	(bad)  
    2d9d:	ff                   	(bad)  
    2d9e:	ff                   	(bad)  
    2d9f:	ff                   	(bad)  
    2da0:	ff                   	(bad)  
    2da1:	ff                   	(bad)  
    2da2:	ff                   	(bad)  
    2da3:	ff                   	(bad)  
    2da4:	ff                   	(bad)  
    2da5:	ff                   	(bad)  
    2da6:	ff                   	(bad)  
    2da7:	ff                   	(bad)  
    2da8:	ff                   	(bad)  
    2da9:	ff                   	(bad)  
    2daa:	ff                   	(bad)  
    2dab:	ff                   	(bad)  
    2dac:	ff                   	(bad)  
    2dad:	ff                   	(bad)  
    2dae:	ff                   	(bad)  
    2daf:	ff                   	(bad)  
    2db0:	ff                   	(bad)  
    2db1:	ff                   	(bad)  
    2db2:	ff                   	(bad)  
    2db3:	ff                   	(bad)  
    2db4:	ff                   	(bad)  
    2db5:	ff                   	(bad)  
    2db6:	ff                   	(bad)  
    2db7:	ff                   	(bad)  
    2db8:	ff                   	(bad)  
    2db9:	ff                   	(bad)  
    2dba:	ff                   	(bad)  
    2dbb:	ff                   	(bad)  
    2dbc:	ff                   	(bad)  
    2dbd:	ff                   	(bad)  
    2dbe:	ff                   	(bad)  
    2dbf:	ff                   	(bad)  
    2dc0:	ff                   	(bad)  
    2dc1:	ff                   	(bad)  
    2dc2:	ff                   	(bad)  
    2dc3:	ff                   	(bad)  
    2dc4:	ff                   	(bad)  
    2dc5:	ff                   	(bad)  
    2dc6:	ff                   	(bad)  
    2dc7:	ff                   	(bad)  
    2dc8:	ff                   	(bad)  
    2dc9:	ff                   	(bad)  
    2dca:	ff                   	(bad)  
    2dcb:	ff                   	(bad)  
    2dcc:	ff                   	(bad)  
    2dcd:	ff                   	(bad)  
    2dce:	ff                   	(bad)  
    2dcf:	ff                   	(bad)  
    2dd0:	ff                   	(bad)  
    2dd1:	ff                   	(bad)  
    2dd2:	ff                   	(bad)  
    2dd3:	ff                   	(bad)  
    2dd4:	ff                   	(bad)  
    2dd5:	ff                   	(bad)  
    2dd6:	ff                   	(bad)  
    2dd7:	ff                   	(bad)  
    2dd8:	ff                   	(bad)  
    2dd9:	ff                   	(bad)  
    2dda:	ff                   	(bad)  
    2ddb:	ff                   	(bad)  
    2ddc:	ff                   	(bad)  
    2ddd:	ff                   	(bad)  
    2dde:	ff                   	(bad)  
    2ddf:	ff                   	(bad)  
    2de0:	ff                   	(bad)  
    2de1:	ff                   	(bad)  
    2de2:	ff                   	(bad)  
    2de3:	ff                   	(bad)  
    2de4:	ff                   	(bad)  
    2de5:	ff                   	(bad)  
    2de6:	ff                   	(bad)  
    2de7:	ff                   	(bad)  
    2de8:	ff                   	(bad)  
    2de9:	ff                   	(bad)  
    2dea:	ff                   	(bad)  
    2deb:	ff                   	(bad)  
    2dec:	ff                   	(bad)  
    2ded:	ff                   	(bad)  
    2dee:	ff                   	(bad)  
    2def:	ff                   	(bad)  
    2df0:	ff                   	(bad)  
    2df1:	ff                   	(bad)  
    2df2:	ff                   	(bad)  
    2df3:	ff                   	(bad)  
    2df4:	ff                   	(bad)  
    2df5:	ff                   	(bad)  
    2df6:	ff                   	(bad)  
    2df7:	ff                   	(bad)  
    2df8:	ff                   	(bad)  
    2df9:	ff                   	(bad)  
    2dfa:	ff                   	(bad)  
    2dfb:	ff                   	(bad)  
    2dfc:	ff                   	(bad)  
    2dfd:	ff                   	(bad)  
    2dfe:	ff                   	(bad)  
    2dff:	ff                   	(bad)  
    2e00:	ff                   	(bad)  
    2e01:	ff                   	(bad)  
    2e02:	ff                   	(bad)  
    2e03:	ff                   	(bad)  
    2e04:	ff                   	(bad)  
    2e05:	ff                   	(bad)  
    2e06:	ff                   	(bad)  
    2e07:	ff                   	(bad)  
    2e08:	ff                   	(bad)  
    2e09:	ff                   	(bad)  
    2e0a:	ff                   	(bad)  
    2e0b:	ff                   	(bad)  
    2e0c:	ff                   	(bad)  
    2e0d:	ff                   	(bad)  
    2e0e:	ff                   	(bad)  
    2e0f:	ff                   	(bad)  
    2e10:	ff                   	(bad)  
    2e11:	ff                   	(bad)  
    2e12:	ff                   	(bad)  
    2e13:	ff                   	(bad)  
    2e14:	ff                   	(bad)  
    2e15:	ff                   	(bad)  
    2e16:	ff                   	(bad)  
    2e17:	ff                   	(bad)  
    2e18:	ff                   	(bad)  
    2e19:	ff                   	(bad)  
    2e1a:	ff                   	(bad)  
    2e1b:	ff                   	(bad)  
    2e1c:	ff                   	(bad)  
    2e1d:	ff                   	(bad)  
    2e1e:	ff                   	(bad)  
    2e1f:	ff                   	(bad)  
    2e20:	ff                   	(bad)  
    2e21:	ff                   	(bad)  
    2e22:	ff                   	(bad)  
    2e23:	ff                   	(bad)  
    2e24:	ff                   	(bad)  
    2e25:	ff                   	(bad)  
    2e26:	ff                   	(bad)  
    2e27:	ff                   	(bad)  
    2e28:	ff                   	(bad)  
    2e29:	ff                   	(bad)  
    2e2a:	ff                   	(bad)  
    2e2b:	ff                   	(bad)  
    2e2c:	ff                   	(bad)  
    2e2d:	ff                   	(bad)  
    2e2e:	ff                   	(bad)  
    2e2f:	ff                   	(bad)  
    2e30:	ff                   	(bad)  
    2e31:	ff                   	(bad)  
    2e32:	ff                   	(bad)  
    2e33:	ff                   	(bad)  
    2e34:	ff                   	(bad)  
    2e35:	ff                   	(bad)  
    2e36:	ff                   	(bad)  
    2e37:	ff                   	(bad)  
    2e38:	ff                   	(bad)  
    2e39:	ff                   	(bad)  
    2e3a:	ff                   	(bad)  
    2e3b:	ff                   	(bad)  
    2e3c:	ff                   	(bad)  
    2e3d:	ff                   	(bad)  
    2e3e:	ff                   	(bad)  
    2e3f:	ff                   	(bad)  
    2e40:	ff                   	(bad)  
    2e41:	ff                   	(bad)  
    2e42:	ff                   	(bad)  
    2e43:	ff                   	(bad)  
    2e44:	ff                   	(bad)  
    2e45:	ff                   	(bad)  
    2e46:	ff                   	(bad)  
    2e47:	ff                   	(bad)  
    2e48:	ff                   	(bad)  
    2e49:	ff                   	(bad)  
    2e4a:	ff                   	(bad)  
    2e4b:	ff                   	(bad)  
    2e4c:	ff                   	(bad)  
    2e4d:	ff                   	(bad)  
    2e4e:	ff                   	(bad)  
    2e4f:	ff                   	(bad)  
    2e50:	ff                   	(bad)  
    2e51:	ff                   	(bad)  
    2e52:	ff                   	(bad)  
    2e53:	ff                   	(bad)  
    2e54:	ff                   	(bad)  
    2e55:	ff                   	(bad)  
    2e56:	ff                   	(bad)  
    2e57:	ff                   	(bad)  
    2e58:	ff                   	(bad)  
    2e59:	ff                   	(bad)  
    2e5a:	ff                   	(bad)  
    2e5b:	ff                   	(bad)  
    2e5c:	ff                   	(bad)  
    2e5d:	ff                   	(bad)  
    2e5e:	ff                   	(bad)  
    2e5f:	ff                   	(bad)  
    2e60:	ff                   	(bad)  
    2e61:	ff                   	(bad)  
    2e62:	ff                   	(bad)  
    2e63:	ff                   	(bad)  
    2e64:	ff                   	(bad)  
    2e65:	ff                   	(bad)  
    2e66:	ff                   	(bad)  
    2e67:	ff                   	(bad)  
    2e68:	ff                   	(bad)  
    2e69:	ff                   	(bad)  
    2e6a:	ff                   	(bad)  
    2e6b:	ff                   	(bad)  
    2e6c:	ff                   	(bad)  
    2e6d:	ff                   	(bad)  
    2e6e:	ff                   	(bad)  
    2e6f:	ff                   	(bad)  
    2e70:	ff                   	(bad)  
    2e71:	ff                   	(bad)  
    2e72:	ff                   	(bad)  
    2e73:	ff                   	(bad)  
    2e74:	ff                   	(bad)  
    2e75:	ff                   	(bad)  
    2e76:	ff                   	(bad)  
    2e77:	ff                   	(bad)  
    2e78:	ff                   	(bad)  
    2e79:	ff                   	(bad)  
    2e7a:	ff                   	(bad)  
    2e7b:	ff                   	(bad)  
    2e7c:	ff                   	(bad)  
    2e7d:	ff                   	(bad)  
    2e7e:	ff                   	(bad)  
    2e7f:	ff                   	(bad)  
    2e80:	ff                   	(bad)  
    2e81:	ff                   	(bad)  
    2e82:	ff                   	(bad)  
    2e83:	ff                   	(bad)  
    2e84:	ff                   	(bad)  
    2e85:	ff                   	(bad)  
    2e86:	ff                   	(bad)  
    2e87:	ff                   	(bad)  
    2e88:	ff                   	(bad)  
    2e89:	ff                   	(bad)  
    2e8a:	ff                   	(bad)  
    2e8b:	ff                   	(bad)  
    2e8c:	ff                   	(bad)  
    2e8d:	ff                   	(bad)  
    2e8e:	ff                   	(bad)  
    2e8f:	ff                   	(bad)  
    2e90:	ff                   	(bad)  
    2e91:	ff                   	(bad)  
    2e92:	ff                   	(bad)  
    2e93:	ff                   	(bad)  
    2e94:	ff                   	(bad)  
    2e95:	ff                   	(bad)  
    2e96:	ff                   	(bad)  
    2e97:	ff                   	(bad)  
    2e98:	ff                   	(bad)  
    2e99:	ff                   	(bad)  
    2e9a:	ff                   	(bad)  
    2e9b:	ff                   	(bad)  
    2e9c:	ff                   	(bad)  
    2e9d:	ff                   	(bad)  
    2e9e:	ff                   	(bad)  
    2e9f:	ff                   	(bad)  
    2ea0:	ff                   	(bad)  
    2ea1:	ff                   	(bad)  
    2ea2:	ff                   	(bad)  
    2ea3:	ff                   	(bad)  
    2ea4:	ff                   	(bad)  
    2ea5:	ff                   	(bad)  
    2ea6:	ff                   	(bad)  
    2ea7:	ff                   	(bad)  
    2ea8:	ff                   	(bad)  
    2ea9:	ff                   	(bad)  
    2eaa:	ff                   	(bad)  
    2eab:	ff                   	(bad)  
    2eac:	ff                   	(bad)  
    2ead:	ff                   	(bad)  
    2eae:	ff                   	(bad)  
    2eaf:	ff                   	(bad)  
    2eb0:	ff                   	(bad)  
    2eb1:	ff                   	(bad)  
    2eb2:	ff                   	(bad)  
    2eb3:	ff                   	(bad)  
    2eb4:	ff                   	(bad)  
    2eb5:	ff                   	(bad)  
    2eb6:	ff                   	(bad)  
    2eb7:	ff                   	(bad)  
    2eb8:	ff                   	(bad)  
    2eb9:	ff                   	(bad)  
    2eba:	ff                   	(bad)  
    2ebb:	ff                   	(bad)  
    2ebc:	ff                   	(bad)  
    2ebd:	ff                   	(bad)  
    2ebe:	ff                   	(bad)  
    2ebf:	ff                   	(bad)  
    2ec0:	ff                   	(bad)  
    2ec1:	ff                   	(bad)  
    2ec2:	ff                   	(bad)  
    2ec3:	ff                   	(bad)  
    2ec4:	ff                   	(bad)  
    2ec5:	ff                   	(bad)  
    2ec6:	ff                   	(bad)  
    2ec7:	ff                   	(bad)  
    2ec8:	ff                   	(bad)  
    2ec9:	ff                   	(bad)  
    2eca:	ff                   	(bad)  
    2ecb:	ff                   	(bad)  
    2ecc:	ff                   	(bad)  
    2ecd:	ff                   	(bad)  
    2ece:	ff                   	(bad)  
    2ecf:	ff                   	(bad)  
    2ed0:	ff                   	(bad)  
    2ed1:	ff                   	(bad)  
    2ed2:	ff                   	(bad)  
    2ed3:	ff                   	(bad)  
    2ed4:	ff                   	(bad)  
    2ed5:	ff                   	(bad)  
    2ed6:	ff                   	(bad)  
    2ed7:	ff                   	(bad)  
    2ed8:	ff                   	(bad)  
    2ed9:	ff                   	(bad)  
    2eda:	ff                   	(bad)  
    2edb:	ff                   	(bad)  
    2edc:	ff                   	(bad)  
    2edd:	ff                   	(bad)  
    2ede:	ff                   	(bad)  
    2edf:	ff                   	(bad)  
    2ee0:	ff                   	(bad)  
    2ee1:	ff                   	(bad)  
    2ee2:	ff                   	(bad)  
    2ee3:	ff                   	(bad)  
    2ee4:	ff                   	(bad)  
    2ee5:	ff                   	(bad)  
    2ee6:	ff                   	(bad)  
    2ee7:	ff                   	(bad)  
    2ee8:	ff                   	(bad)  
    2ee9:	ff                   	(bad)  
    2eea:	ff                   	(bad)  
    2eeb:	ff                   	(bad)  
    2eec:	ff                   	(bad)  
    2eed:	ff                   	(bad)  
    2eee:	ff                   	(bad)  
    2eef:	ff                   	(bad)  
    2ef0:	ff                   	(bad)  
    2ef1:	ff                   	(bad)  
    2ef2:	ff                   	(bad)  
    2ef3:	ff                   	(bad)  
    2ef4:	ff                   	(bad)  
    2ef5:	ff                   	(bad)  
    2ef6:	ff                   	(bad)  
    2ef7:	ff                   	(bad)  
    2ef8:	ff                   	(bad)  
    2ef9:	ff                   	(bad)  
    2efa:	ff                   	(bad)  
    2efb:	ff                   	(bad)  
    2efc:	ff                   	(bad)  
    2efd:	ff                   	(bad)  
    2efe:	ff                   	(bad)  
    2eff:	ff                   	(bad)  
    2f00:	ff                   	(bad)  
    2f01:	ff                   	(bad)  
    2f02:	ff                   	(bad)  
    2f03:	ff                   	(bad)  
    2f04:	ff                   	(bad)  
    2f05:	ff                   	(bad)  
    2f06:	ff                   	(bad)  
    2f07:	ff                   	(bad)  
    2f08:	ff                   	(bad)  
    2f09:	ff                   	(bad)  
    2f0a:	ff                   	(bad)  
    2f0b:	ff                   	(bad)  
    2f0c:	ff                   	(bad)  
    2f0d:	ff                   	(bad)  
    2f0e:	ff                   	(bad)  
    2f0f:	ff                   	(bad)  
    2f10:	ff                   	(bad)  
    2f11:	ff                   	(bad)  
    2f12:	ff                   	(bad)  
    2f13:	ff                   	(bad)  
    2f14:	ff                   	(bad)  
    2f15:	ff                   	(bad)  
    2f16:	ff                   	(bad)  
    2f17:	ff                   	(bad)  
    2f18:	ff                   	(bad)  
    2f19:	ff                   	(bad)  
    2f1a:	ff                   	(bad)  
    2f1b:	ff                   	(bad)  
    2f1c:	ff                   	(bad)  
    2f1d:	ff                   	(bad)  
    2f1e:	ff                   	(bad)  
    2f1f:	ff                   	(bad)  
    2f20:	ff                   	(bad)  
    2f21:	ff                   	(bad)  
    2f22:	ff                   	(bad)  
    2f23:	ff                   	(bad)  
    2f24:	ff                   	(bad)  
    2f25:	ff                   	(bad)  
    2f26:	ff                   	(bad)  
    2f27:	ff                   	(bad)  
    2f28:	ff                   	(bad)  
    2f29:	ff                   	(bad)  
    2f2a:	ff                   	(bad)  
    2f2b:	ff                   	(bad)  
    2f2c:	ff                   	(bad)  
    2f2d:	ff                   	(bad)  
    2f2e:	ff                   	(bad)  
    2f2f:	ff                   	(bad)  
    2f30:	ff                   	(bad)  
    2f31:	ff                   	(bad)  
    2f32:	ff                   	(bad)  
    2f33:	ff                   	(bad)  
    2f34:	ff                   	(bad)  
    2f35:	ff                   	(bad)  
    2f36:	ff                   	(bad)  
    2f37:	ff                   	(bad)  
    2f38:	ff                   	(bad)  
    2f39:	ff                   	(bad)  
    2f3a:	ff                   	(bad)  
    2f3b:	ff                   	(bad)  
    2f3c:	ff                   	(bad)  
    2f3d:	ff                   	(bad)  
    2f3e:	ff                   	(bad)  
    2f3f:	ff                   	(bad)  
    2f40:	ff                   	(bad)  
    2f41:	ff                   	(bad)  
    2f42:	ff                   	(bad)  
    2f43:	ff                   	(bad)  
    2f44:	ff                   	(bad)  
    2f45:	ff                   	(bad)  
    2f46:	ff                   	(bad)  
    2f47:	ff                   	(bad)  
    2f48:	ff                   	(bad)  
    2f49:	ff                   	(bad)  
    2f4a:	ff                   	(bad)  
    2f4b:	ff                   	(bad)  
    2f4c:	ff                   	(bad)  
    2f4d:	ff                   	(bad)  
    2f4e:	ff                   	(bad)  
    2f4f:	ff                   	(bad)  
    2f50:	ff                   	(bad)  
    2f51:	ff                   	(bad)  
    2f52:	ff                   	(bad)  
    2f53:	ff                   	(bad)  
    2f54:	ff                   	(bad)  
    2f55:	ff                   	(bad)  
    2f56:	ff                   	(bad)  
    2f57:	ff                   	(bad)  
    2f58:	ff                   	(bad)  
    2f59:	ff                   	(bad)  
    2f5a:	ff                   	(bad)  
    2f5b:	ff                   	(bad)  
    2f5c:	ff                   	(bad)  
    2f5d:	ff                   	(bad)  
    2f5e:	ff                   	(bad)  
    2f5f:	ff                   	(bad)  
    2f60:	ff                   	(bad)  
    2f61:	ff                   	(bad)  
    2f62:	ff                   	(bad)  
    2f63:	ff                   	(bad)  
    2f64:	ff                   	(bad)  
    2f65:	ff                   	(bad)  
    2f66:	ff                   	(bad)  
    2f67:	ff                   	(bad)  
    2f68:	ff                   	(bad)  
    2f69:	ff                   	(bad)  
    2f6a:	ff                   	(bad)  
    2f6b:	ff                   	(bad)  
    2f6c:	ff                   	(bad)  
    2f6d:	ff                   	(bad)  
    2f6e:	ff                   	(bad)  
    2f6f:	ff                   	(bad)  
    2f70:	ff                   	(bad)  
    2f71:	ff                   	(bad)  
    2f72:	ff                   	(bad)  
    2f73:	ff                   	(bad)  
    2f74:	ff                   	(bad)  
    2f75:	ff                   	(bad)  
    2f76:	ff                   	(bad)  
    2f77:	ff                   	(bad)  
    2f78:	ff                   	(bad)  
    2f79:	ff                   	(bad)  
    2f7a:	ff                   	(bad)  
    2f7b:	ff                   	(bad)  
    2f7c:	ff                   	(bad)  
    2f7d:	ff                   	(bad)  
    2f7e:	ff                   	(bad)  
    2f7f:	ff                   	(bad)  
    2f80:	ff                   	(bad)  
    2f81:	ff                   	(bad)  
    2f82:	ff                   	(bad)  
    2f83:	ff                   	(bad)  
    2f84:	ff                   	(bad)  
    2f85:	ff                   	(bad)  
    2f86:	ff                   	(bad)  
    2f87:	ff                   	(bad)  
    2f88:	ff                   	(bad)  
    2f89:	ff                   	(bad)  
    2f8a:	ff                   	(bad)  
    2f8b:	ff                   	(bad)  
    2f8c:	ff                   	(bad)  
    2f8d:	ff                   	(bad)  
    2f8e:	ff                   	(bad)  
    2f8f:	ff                   	(bad)  
    2f90:	ff                   	(bad)  
    2f91:	ff                   	(bad)  
    2f92:	ff                   	(bad)  
    2f93:	ff                   	(bad)  
    2f94:	ff                   	(bad)  
    2f95:	ff                   	(bad)  
    2f96:	ff                   	(bad)  
    2f97:	ff                   	(bad)  
    2f98:	ff                   	(bad)  
    2f99:	ff                   	(bad)  
    2f9a:	ff                   	(bad)  
    2f9b:	ff                   	(bad)  
    2f9c:	ff                   	(bad)  
    2f9d:	ff                   	(bad)  
    2f9e:	ff                   	(bad)  
    2f9f:	ff                   	(bad)  
    2fa0:	ff                   	(bad)  
    2fa1:	ff                   	(bad)  
    2fa2:	ff                   	(bad)  
    2fa3:	ff                   	(bad)  
    2fa4:	ff                   	(bad)  
    2fa5:	ff                   	(bad)  
    2fa6:	ff                   	(bad)  
    2fa7:	ff                   	(bad)  
    2fa8:	ff                   	(bad)  
    2fa9:	ff                   	(bad)  
    2faa:	ff                   	(bad)  
    2fab:	ff                   	(bad)  
    2fac:	ff                   	(bad)  
    2fad:	ff                   	(bad)  
    2fae:	ff                   	(bad)  
    2faf:	ff                   	(bad)  
    2fb0:	ff                   	(bad)  
    2fb1:	ff                   	(bad)  
    2fb2:	ff                   	(bad)  
    2fb3:	ff                   	(bad)  
    2fb4:	ff                   	(bad)  
    2fb5:	ff                   	(bad)  
    2fb6:	ff                   	(bad)  
    2fb7:	ff                   	(bad)  
    2fb8:	ff                   	(bad)  
    2fb9:	ff                   	(bad)  
    2fba:	ff                   	(bad)  
    2fbb:	ff                   	(bad)  
    2fbc:	ff                   	(bad)  
    2fbd:	ff                   	(bad)  
    2fbe:	ff                   	(bad)  
    2fbf:	ff                   	(bad)  
    2fc0:	ff                   	(bad)  
    2fc1:	ff                   	(bad)  
    2fc2:	ff                   	(bad)  
    2fc3:	ff                   	(bad)  
    2fc4:	ff                   	(bad)  
    2fc5:	ff                   	(bad)  
    2fc6:	ff                   	(bad)  
    2fc7:	ff                   	(bad)  
    2fc8:	ff                   	(bad)  
    2fc9:	ff                   	(bad)  
    2fca:	ff                   	(bad)  
    2fcb:	ff                   	(bad)  
    2fcc:	ff                   	(bad)  
    2fcd:	ff                   	(bad)  
    2fce:	ff                   	(bad)  
    2fcf:	ff                   	(bad)  
    2fd0:	ff                   	(bad)  
    2fd1:	ff                   	(bad)  
    2fd2:	ff                   	(bad)  
    2fd3:	ff                   	(bad)  
    2fd4:	ff                   	(bad)  
    2fd5:	ff                   	(bad)  
    2fd6:	ff                   	(bad)  
    2fd7:	ff                   	(bad)  
    2fd8:	ff                   	(bad)  
    2fd9:	ff                   	(bad)  
    2fda:	ff                   	(bad)  
    2fdb:	ff                   	(bad)  
    2fdc:	ff                   	(bad)  
    2fdd:	ff                   	(bad)  
    2fde:	ff                   	(bad)  
    2fdf:	ff                   	(bad)  
    2fe0:	ff                   	(bad)  
    2fe1:	ff                   	(bad)  
    2fe2:	ff                   	(bad)  
    2fe3:	ff                   	(bad)  
    2fe4:	ff                   	(bad)  
    2fe5:	ff                   	(bad)  
    2fe6:	ff                   	(bad)  
    2fe7:	ff                   	(bad)  
    2fe8:	ff                   	(bad)  
    2fe9:	ff                   	(bad)  
    2fea:	ff                   	(bad)  
    2feb:	ff                   	(bad)  
    2fec:	ff                   	(bad)  
    2fed:	ff                   	(bad)  
    2fee:	ff                   	(bad)  
    2fef:	ff                   	(bad)  
    2ff0:	ff                   	(bad)  
    2ff1:	ff                   	(bad)  
    2ff2:	ff                   	(bad)  
    2ff3:	ff                   	(bad)  
    2ff4:	ff                   	(bad)  
    2ff5:	ff                   	(bad)  
    2ff6:	ff                   	(bad)  
    2ff7:	ff                   	(bad)  
    2ff8:	ff                   	(bad)  
    2ff9:	ff                   	(bad)  
    2ffa:	ff                   	(bad)  
    2ffb:	ff                   	(bad)  
    2ffc:	ff                   	(bad)  
    2ffd:	ff                   	(bad)  
    2ffe:	ff                   	(bad)  
    2fff:	ff 66 60             	jmp    *0x60(%bp)
    3002:	0f a8                	push   %gs
    3004:	0f a0                	push   %fs
    3006:	06                   	push   %es
    3007:	1e                   	push   %ds
    3008:	0e                   	push   %cs
    3009:	1f                   	pop    %ds
    300a:	c7 06 94 54 30 55    	movw   $0x5530,0x5494
    3010:	8c 1e 96 54          	mov    %ds,0x5496
    3014:	fb                   	sti    
    3015:	8b f8                	mov    %ax,%di
    3017:	33 f6                	xor    %si,%si
    3019:	b9 10 00             	mov    $0x10,%cx
    301c:	ba 69 10             	mov    $0x1069,%dx
    301f:	b8 02 b1             	mov    $0xb102,%ax
    3022:	cd 1a                	int    $0x1a
    3024:	b0 00                	mov    $0x0,%al
    3026:	73 09                	jae    0x3031
    3028:	be 2f 53             	mov    $0x532f,%si
    302b:	e8 cb e0             	call   0x10f9
    302e:	e9 36 02             	jmp    0x3267
    3031:	83 e3 f8             	and    $0xfff8,%bx
    3034:	83 e7 f8             	and    $0xfff8,%di
    3037:	3b df                	cmp    %di,%bx
    3039:	0f 85 49 02          	jne    0x3286
    303d:	e8 12 09             	call   0x3952
    3040:	0f 84 23 02          	je     0x3267
    3044:	0f b6 36 68 01       	movzbw 0x168,%si
    3049:	c1 e6 02             	shl    $0x2,%si
    304c:	66 8b 84 04 51       	mov    0x5104(%si),%eax
    3051:	66 a3 78 01          	mov    %eax,0x178
    3055:	c6 06 78 01 28       	movb   $0x28,0x178
    305a:	66 33 c0             	xor    %eax,%eax
    305d:	8c d8                	mov    %ds,%ax
    305f:	66 c1 e0 04          	shl    $0x4,%eax
    3063:	66 a3 8c 01          	mov    %eax,0x18c
    3067:	66 33 ed             	xor    %ebp,%ebp
    306a:	c4 2e 94 54          	les    0x5494,%bp
    306e:	0f 20 c0             	mov    %cr0,%eax
    3071:	66 26 89 86 ec 02    	mov    %eax,%es:0x2ec(%bp)
    3077:	e8 0e e2             	call   0x1288
    307a:	e8 7a e1             	call   0x11f7
    307d:	be 4b 46             	mov    $0x464b,%si
    3080:	e8 76 e0             	call   0x10f9
    3083:	be 70 01             	mov    $0x170,%si
    3086:	e8 70 e0             	call   0x10f9
    3089:	e8 7f e0             	call   0x110b
    308c:	be 21 46             	mov    $0x4621,%si
    308f:	e8 67 e0             	call   0x10f9
    3092:	bb 7e 00             	mov    $0x7e,%bx
    3095:	e8 31 e1             	call   0x11c9
    3098:	3d 00 25             	cmp    $0x2500,%ax
    309b:	75 2f                	jne    0x30cc
    309d:	be 6a 52             	mov    $0x526a,%si
    30a0:	e8 56 e0             	call   0x10f9
    30a3:	e8 48 e1             	call   0x11ee
    30a6:	2c 30                	sub    $0x30,%al
    30a8:	3c 07                	cmp    $0x7,%al
    30aa:	77 20                	ja     0x30cc
    30ac:	0c 80                	or     $0x80,%al
    30ae:	a2 87 01             	mov    %al,0x187
    30b1:	e8 07 e1             	call   0x11bb
    30b4:	0f b6 1e 87 01       	movzbw 0x187,%bx
    30b9:	83 e3 03             	and    $0x3,%bx
    30bc:	d1 e3                	shl    %bx
    30be:	8b 87 5c 54          	mov    0x545c(%bx),%ax
    30c2:	a3 88 01             	mov    %ax,0x188
    30c5:	8b 87 64 54          	mov    0x5464(%bx),%ax
    30c9:	a3 8a 01             	mov    %ax,0x18a
    30cc:	8e 26 00 1c          	mov    0x1c00,%fs
    30d0:	64 a0 75 00          	mov    %fs:0x75,%al
    30d4:	a2 d0 00             	mov    %al,0xd0
    30d7:	c7 06 70 54 00 00    	movw   $0x0,0x5470
    30dd:	c7 06 72 54 00 00    	movw   $0x0,0x5472
    30e3:	33 db                	xor    %bx,%bx
    30e5:	c1 e3 02             	shl    $0x2,%bx
    30e8:	66 8b 87 10 01       	mov    0x110(%bx),%eax
    30ed:	66 26 89 86 e4 02    	mov    %eax,%es:0x2e4(%bp)
    30f3:	c1 eb 02             	shr    $0x2,%bx
    30f6:	e8 78 e4             	call   0x1571
    30f9:	e8 19 e4             	call   0x1515
    30fc:	43                   	inc    %bx
    30fd:	3a 1e 55 01          	cmp    0x155,%bl
    3101:	72 e2                	jb     0x30e5
    3103:	26 c6 86 e2 02 00    	movb   $0x0,%es:0x2e2(%bp)
    3109:	26 0f b6 9e e2 02    	movzbw %es:0x2e2(%bp),%bx
    310f:	c6 87 d1 00 00       	movb   $0x0,0xd1(%bx)
    3114:	d1 e3                	shl    %bx
    3116:	8b 87 a0 00          	mov    0xa0(%bx),%ax
    311a:	26 89 86 ea 02       	mov    %ax,%es:0x2ea(%bp)
    311f:	d1 e3                	shl    %bx
    3121:	66 8b 87 10 01       	mov    0x110(%bx),%eax
    3126:	66 26 89 86 e4 02    	mov    %eax,%es:0x2e4(%bp)
    312c:	e8 09 09             	call   0x3a38
    312f:	e8 a8 01             	call   0x32da
    3132:	72 07                	jb     0x313b
    3134:	e8 c8 04             	call   0x35ff
    3137:	0f 83 50 01          	jae    0x328b
    313b:	83 0e 72 54 01       	orw    $0x1,0x5472
    3140:	e8 2e e4             	call   0x1571
    3143:	26 fe 86 e2 02       	incb   %es:0x2e2(%bp)
    3148:	26 0f b6 86 e2 02    	movzbw %es:0x2e2(%bp),%ax
    314e:	3a 06 55 01          	cmp    0x155,%al
    3152:	73 12                	jae    0x3166
    3154:	40                   	inc    %ax
    3155:	be 62 46             	mov    $0x4662,%si
    3158:	e8 9e df             	call   0x10f9
    315b:	e8 2d e0             	call   0x118b
    315e:	be 78 46             	mov    $0x4678,%si
    3161:	e8 95 df             	call   0x10f9
    3164:	eb a3                	jmp    0x3109
    3166:	f7 06 72 54 01 00    	testw  $0x1,0x5472
    316c:	be 41 46             	mov    $0x4641,%si
    316f:	74 03                	je     0x3174
    3171:	be b1 4b             	mov    $0x4bb1,%si
    3174:	e8 82 df             	call   0x10f9
    3177:	bb b4 00             	mov    $0xb4,%bx
    317a:	e8 4c e0             	call   0x11c9
    317d:	e8 52 0d             	call   0x3ed2
    3180:	fb                   	sti    
    3181:	33 c9                	xor    %cx,%cx
    3183:	b6 00                	mov    $0x0,%dh
    3185:	b0 00                	mov    $0x0,%al
    3187:	c4 1e 94 54          	les    0x5494,%bx
    318b:	b4 ff                	mov    $0xff,%ah
    318d:	b2 8f                	mov    $0x8f,%dl
    318f:	cd 13                	int    $0x13
    3191:	72 09                	jb     0x319c
    3193:	3d 00 04             	cmp    $0x400,%ax
    3196:	72 04                	jb     0x319c
    3198:	88 36 54 01          	mov    %dh,0x154
    319c:	80 3e e1 1b 00       	cmpb   $0x0,0x1be1
    31a1:	75 3d                	jne    0x31e0
    31a3:	f6 06 56 01 01       	testb  $0x1,0x156
    31a8:	75 4f                	jne    0x31f9
    31aa:	8e 26 00 1c          	mov    0x1c00,%fs
    31ae:	80 3e e4 1b 00       	cmpb   $0x0,0x1be4
    31b3:	74 0c                	je     0x31c1
    31b5:	80 3e e7 1b 80       	cmpb   $0x80,0x1be7
    31ba:	75 05                	jne    0x31c1
    31bc:	64 fe 06 75 00       	incb   %fs:0x75
    31c1:	64 a0 75 00          	mov    %fs:0x75,%al
    31c5:	02 06 e3 1b          	add    0x1be3,%al
    31c9:	02 06 e4 1b          	add    0x1be4,%al
    31cd:	38 06 d0 00          	cmp    %al,0xd0
    31d1:	74 26                	je     0x31f9
    31d3:	64 83 0e 10 00 01    	orw    $0x1,%fs:0x10
    31d9:	80 3e e3 1b 00       	cmpb   $0x0,0x1be3
    31de:	74 19                	je     0x31f9
    31e0:	8e 26 02 1c          	mov    0x1c02,%fs
    31e4:	66 64 a1 64 00       	mov    %fs:0x64,%eax
    31e9:	66 a3 5c 01          	mov    %eax,0x15c
    31ed:	64 c7 06 64 00 59 03 	movw   $0x359,%fs:0x64
    31f4:	64 8c 0e 66 00       	mov    %cs,%fs:0x66
    31f9:	8e 26 02 1c          	mov    0x1c02,%fs
    31fd:	80 3e d0 00 00       	cmpb   $0x0,0xd0
    3202:	75 0a                	jne    0x320e
    3204:	66 64 a1 4c 00       	mov    %fs:0x4c,%eax
    3209:	66 64 a3 00 01       	mov    %eax,%fs:0x100
    320e:	66 64 a1 4c 00       	mov    %fs:0x4c,%eax
    3213:	66 a3 50 01          	mov    %eax,0x150
    3217:	64 c7 06 4c 00 00 02 	movw   $0x200,%fs:0x4c
    321e:	64 8c 0e 4e 00       	mov    %cs,%fs:0x4e
    3223:	66 64 a1 00 01       	mov    %fs:0x100,%eax
    3228:	66 a3 58 01          	mov    %eax,0x158
    322c:	64 c7 06 00 01 f0 02 	movw   $0x2f0,%fs:0x100
    3233:	64 8c 0e 02 01       	mov    %cs,%fs:0x102
    3238:	66 64 a1 64 00       	mov    %fs:0x64,%eax
    323d:	66 a3 5c 01          	mov    %eax,0x15c
    3241:	64 c7 06 64 00 59 03 	movw   $0x359,%fs:0x64
    3248:	64 8c 0e 66 00       	mov    %cs,%fs:0x66
    324d:	80 3e e4 1b 00       	cmpb   $0x0,0x1be4
    3252:	74 0b                	je     0x325f
    3254:	80 3e e7 1b 80       	cmpb   $0x80,0x1be7
    3259:	75 04                	jne    0x325f
    325b:	fe 06 d0 00          	incb   0xd0
    325f:	be e1 51             	mov    $0x51e1,%si
    3262:	e8 94 de             	call   0x10f9
    3265:	b0 18                	mov    $0x18,%al
    3267:	a2 02 00             	mov    %al,0x2
    326a:	b9 00 30             	mov    $0x3000,%cx
    326d:	33 db                	xor    %bx,%bx
    326f:	b0 00                	mov    $0x0,%al
    3271:	02 07                	add    (%bx),%al
    3273:	43                   	inc    %bx
    3274:	e2 fb                	loop   0x3271
    3276:	4b                   	dec    %bx
    3277:	f6 d0                	not    %al
    3279:	88 07                	mov    %al,(%bx)
    327b:	33 c0                	xor    %ax,%ax
    327d:	1f                   	pop    %ds
    327e:	07                   	pop    %es
    327f:	0f a1                	pop    %fs
    3281:	0f a9                	pop    %gs
    3283:	66 61                	popal  
    3285:	cb                   	lret   
    3286:	a2 00 00             	mov    %al,0x0
    3289:	eb dc                	jmp    0x3267
    328b:	e8 7d de             	call   0x110b
    328e:	a0 58 54             	mov    0x5458,%al
    3291:	0a c0                	or     %al,%al
    3293:	75 09                	jne    0x329e
    3295:	be eb 46             	mov    $0x46eb,%si
    3298:	e8 5e de             	call   0x10f9
    329b:	e9 a2 fe             	jmp    0x3140
    329e:	f6 06 56 01 01       	testb  $0x1,0x156
    32a3:	74 0f                	je     0x32b4
    32a5:	be 49 4a             	mov    $0x4a49,%si
    32a8:	e8 ea 02             	call   0x3595
    32ab:	be 3c 4a             	mov    $0x4a3c,%si
    32ae:	e8 48 de             	call   0x10f9
    32b1:	e9 8c fe             	jmp    0x3140
    32b4:	8e 26 00 1c          	mov    0x1c00,%fs
    32b8:	64 00 06 75 00       	add    %al,%fs:0x75
    32bd:	00 06 57 01          	add    %al,0x157
    32c1:	26 0f b6 9e e2 02    	movzbw %es:0x2e2(%bp),%bx
    32c7:	88 87 d1 00          	mov    %al,0xd1(%bx)
    32cb:	be 30 4a             	mov    $0x4a30,%si
    32ce:	e8 c4 02             	call   0x3595
    32d1:	be 23 4a             	mov    $0x4a23,%si
    32d4:	e8 22 de             	call   0x10f9
    32d7:	e9 66 fe             	jmp    0x3140
    32da:	83 26 72 54 fd       	andw   $0xfffd,0x5472
    32df:	e8 8f e2             	call   0x1571
    32e2:	e8 30 e2             	call   0x1515
    32e5:	33 ff                	xor    %di,%di
    32e7:	c6 06 5a 54 00       	movb   $0x0,0x545a
    32ec:	b8 04 00             	mov    $0x4,%ax
    32ef:	e8 26 06             	call   0x3918
    32f2:	8e 26 00 1c          	mov    0x1c00,%fs
    32f6:	66 64 8b 1e 6c 00    	mov    %fs:0x6c,%ebx
    32fc:	66 81 c3 70 08 00 00 	add    $0x870,%ebx
    3303:	8e 26 00 1c          	mov    0x1c00,%fs
    3307:	66 64 8b 0e 6c 00    	mov    %fs:0x6c,%ecx
    330d:	66 83 c1 24          	add    $0x24,%ecx
    3311:	e8 f2 e1             	call   0x1506
    3314:	a8 02                	test   $0x2,%al
    3316:	74 64                	je     0x337c
    3318:	e8 29 e2             	call   0x1544
    331b:	a8 04                	test   $0x4,%al
    331d:	74 14                	je     0x3333
    331f:	e8 8c 00             	call   0x33ae
    3322:	73 ce                	jae    0x32f2
    3324:	80 3e 5a 54 00       	cmpb   $0x0,0x545a
    3329:	75 af                	jne    0x32da
    332b:	be 33 47             	mov    $0x4733,%si
    332e:	e8 c8 dd             	call   0x10f9
    3331:	f9                   	stc    
    3332:	c3                   	ret    
    3333:	a8 08                	test   $0x8,%al
    3335:	74 15                	je     0x334c
    3337:	34 08                	xor    $0x8,%al
    3339:	e8 17 e2             	call   0x1553
    333c:	0b ff                	or     %di,%di
    333e:	75 03                	jne    0x3343
    3340:	e8 c8 dd             	call   0x110b
    3343:	be 0e 4a             	mov    $0x4a0e,%si
    3346:	e8 b0 dd             	call   0x10f9
    3349:	47                   	inc    %di
    334a:	eb a6                	jmp    0x32f2
    334c:	8e 26 00 1c          	mov    0x1c00,%fs
    3350:	0b ff                	or     %di,%di
    3352:	74 0d                	je     0x3361
    3354:	66 64 3b 0e 6c 00    	cmp    %fs:0x6c,%ecx
    335a:	77 05                	ja     0x3361
    335c:	e8 2c dd             	call   0x108b
    335f:	eb a2                	jmp    0x3303
    3361:	66 64 3b 1e 6c 00    	cmp    %fs:0x6c,%ebx
    3367:	72 03                	jb     0x336c
    3369:	f4                   	hlt    
    336a:	eb a5                	jmp    0x3311
    336c:	be 82 46             	mov    $0x4682,%si
    336f:	e8 87 dd             	call   0x10f9
    3372:	eb bd                	jmp    0x3331
    3374:	b0 01                	mov    $0x1,%al
    3376:	e8 bc e1             	call   0x1535
    3379:	e8 99 e1             	call   0x1515
    337c:	8e 26 00 1c          	mov    0x1c00,%fs
    3380:	66 64 8b 1e 6c 00    	mov    %fs:0x6c,%ebx
    3386:	66 83 c3 04          	add    $0x4,%ebx
    338a:	e8 99 e1             	call   0x1526
    338d:	a8 01                	test   $0x1,%al
    338f:	75 e3                	jne    0x3374
    3391:	8e 26 00 1c          	mov    0x1c00,%fs
    3395:	66 64 3b 1e 6c 00    	cmp    %fs:0x6c,%ebx
    339b:	72 ed                	jb     0x338a
    339d:	e8 d1 e1             	call   0x1571
    33a0:	f7 06 72 54 02 00    	testw  $0x2,0x5472
    33a6:	74 8a                	je     0x3332
    33a8:	e8 54 02             	call   0x35ff
    33ab:	e9 7d ff             	jmp    0x332b
    33ae:	e8 93 e1             	call   0x1544
    33b1:	24 f0                	and    $0xf0,%al
    33b3:	75 58                	jne    0x340d
    33b5:	be 07 47             	mov    $0x4707,%si
    33b8:	e8 3e dd             	call   0x10f9
    33bb:	66 ba 09 10 00 00    	mov    $0x1009,%edx
    33c1:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    33c7:	e8 64 df             	call   0x132e
    33ca:	e8 b1 dd             	call   0x117e
    33cd:	be d8 51             	mov    $0x51d8,%si
    33d0:	e8 26 dd             	call   0x10f9
    33d3:	66 ba 08 10 00 00    	mov    $0x1008,%edx
    33d9:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    33df:	e8 4c df             	call   0x132e
    33e2:	e8 99 dd             	call   0x117e
    33e5:	83 0e 72 54 02       	orw    $0x2,0x5472
    33ea:	be 22 47             	mov    $0x4722,%si
    33ed:	b0 00                	mov    $0x0,%al
    33ef:	e8 07 dd             	call   0x10f9
    33f2:	50                   	push   %ax
    33f3:	b0 00                	mov    $0x0,%al
    33f5:	e8 5b e1             	call   0x1553
    33f8:	58                   	pop    %ax
    33f9:	33 ff                	xor    %di,%di
    33fb:	3c 01                	cmp    $0x1,%al
    33fd:	f5                   	cmc    
    33fe:	c3                   	ret    
    33ff:	be ae 47             	mov    $0x47ae,%si
    3402:	b0 01                	mov    $0x1,%al
    3404:	eb e9                	jmp    0x33ef
    3406:	83 0e 72 54 01       	orw    $0x1,0x5472
    340b:	eb e0                	jmp    0x33ed
    340d:	be a4 48             	mov    $0x48a4,%si
    3410:	3c f0                	cmp    $0xf0,%al
    3412:	74 ee                	je     0x3402
    3414:	be 4b 47             	mov    $0x474b,%si
    3417:	3c 80                	cmp    $0x80,%al
    3419:	74 e7                	je     0x3402
    341b:	be 77 47             	mov    $0x4777,%si
    341e:	3c 40                	cmp    $0x40,%al
    3420:	74 e0                	je     0x3402
    3422:	be eb 47             	mov    $0x47eb,%si
    3425:	3c 20                	cmp    $0x20,%al
    3427:	74 d9                	je     0x3402
    3429:	be 1f 48             	mov    $0x481f,%si
    342c:	3c 30                	cmp    $0x30,%al
    342e:	74 d6                	je     0x3406
    3430:	be 63 48             	mov    $0x4863,%si
    3433:	3c 50                	cmp    $0x50,%al
    3435:	74 cf                	je     0x3406
    3437:	be d3 48             	mov    $0x48d3,%si
    343a:	3c 60                	cmp    $0x60,%al
    343c:	74 c8                	je     0x3406
    343e:	be 24 49             	mov    $0x4924,%si
    3441:	3c b0                	cmp    $0xb0,%al
    3443:	74 c1                	je     0x3406
    3445:	be 75 49             	mov    $0x4975,%si
    3448:	3c 70                	cmp    $0x70,%al
    344a:	74 a1                	je     0x33ed
    344c:	be 9e 49             	mov    $0x499e,%si
    344f:	3c e0                	cmp    $0xe0,%al
    3451:	74 9a                	je     0x33ed
    3453:	3c d0                	cmp    $0xd0,%al
    3455:	0f 85 b0 00          	jne    0x3509
    3459:	be 38 51             	mov    $0x5138,%si
    345c:	e8 9a dc             	call   0x10f9
    345f:	b0 00                	mov    $0x0,%al
    3461:	e8 ef e0             	call   0x1553
    3464:	b8 12 00             	mov    $0x12,%ax
    3467:	e8 ae 04             	call   0x3918
    346a:	26 8b 9e ea 02       	mov    %es:0x2ea(%bp),%bx
    346f:	83 e3 f8             	and    $0xfff8,%bx
    3472:	e8 13 06             	call   0x3a88
    3475:	33 ff                	xor    %di,%di
    3477:	b9 40 00             	mov    $0x40,%cx
    347a:	8a 85 b0 54          	mov    0x54b0(%di),%al
    347e:	88 85 f0 54          	mov    %al,0x54f0(%di)
    3482:	47                   	inc    %di
    3483:	e2 f5                	loop   0x347a
    3485:	26 8b 9e ea 02       	mov    %es:0x2ea(%bp),%bx
    348a:	e8 fb 05             	call   0x3a88
    348d:	83 e3 f8             	and    $0xfff8,%bx
    3490:	b9 40 00             	mov    $0x40,%cx
    3493:	bf 3e 00             	mov    $0x3e,%di
    3496:	b8 0c b1             	mov    $0xb10c,%ax
    3499:	cd 1a                	int    $0x1a
    349b:	b9 20 00             	mov    $0x20,%cx
    349e:	bf 40 00             	mov    $0x40,%di
    34a1:	b8 0c b1             	mov    $0xb10c,%ax
    34a4:	cd 1a                	int    $0x1a
    34a6:	b9 00 00             	mov    $0x0,%cx
    34a9:	bf 3e 00             	mov    $0x3e,%di
    34ac:	b8 0c b1             	mov    $0xb10c,%ax
    34af:	cd 1a                	int    $0x1a
    34b1:	bf 40 00             	mov    $0x40,%di
    34b4:	b8 0c b1             	mov    $0xb10c,%ax
    34b7:	cd 1a                	int    $0x1a
    34b9:	b9 40 00             	mov    $0x40,%cx
    34bc:	bf 04 00             	mov    $0x4,%di
    34bf:	b8 0c b1             	mov    $0xb10c,%ax
    34c2:	cd 1a                	int    $0x1a
    34c4:	b8 7e 00             	mov    $0x7e,%ax
    34c7:	e8 4e 04             	call   0x3918
    34ca:	26 8b 9e ea 02       	mov    %es:0x2ea(%bp),%bx
    34cf:	bf 00 00             	mov    $0x0,%di
    34d2:	b8 0a b1             	mov    $0xb10a,%ax
    34d5:	cd 1a                	int    $0x1a
    34d7:	b8 0d b1             	mov    $0xb10d,%ax
    34da:	e8 ae 05             	call   0x3a8b
    34dd:	33 ff                	xor    %di,%di
    34df:	b9 40 00             	mov    $0x40,%cx
    34e2:	8a 85 f0 54          	mov    0x54f0(%di),%al
    34e6:	88 85 b0 54          	mov    %al,0x54b0(%di)
    34ea:	47                   	inc    %di
    34eb:	e2 f5                	loop   0x34e2
    34ed:	83 e3 f8             	and    $0xfff8,%bx
    34f0:	b8 0d b1             	mov    $0xb10d,%ax
    34f3:	e8 95 05             	call   0x3a8b
    34f6:	b8 7e 00             	mov    $0x7e,%ax
    34f9:	e8 1c 04             	call   0x3918
    34fc:	be 80 51             	mov    $0x5180,%si
    34ff:	e8 f7 db             	call   0x10f9
    3502:	c6 06 5a 54 01       	movb   $0x1,0x545a
    3507:	f9                   	stc    
    3508:	c3                   	ret    
    3509:	3c 90                	cmp    $0x90,%al
    350b:	75 7d                	jne    0x358a
    350d:	83 0e 72 54 02       	orw    $0x2,0x5472
    3512:	66 ba 0b 10 00 00    	mov    $0x100b,%edx
    3518:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    351e:	e8 0d de             	call   0x132e
    3521:	3c ff                	cmp    $0xff,%al
    3523:	75 08                	jne    0x352d
    3525:	be e4 49             	mov    $0x49e4,%si
    3528:	e8 ce db             	call   0x10f9
    352b:	eb 21                	jmp    0x354e
    352d:	be c2 49             	mov    $0x49c2,%si
    3530:	e8 c6 db             	call   0x10f9
    3533:	e8 48 dc             	call   0x117e
    3536:	be d8 51             	mov    $0x51d8,%si
    3539:	e8 bd db             	call   0x10f9
    353c:	66 ba 0a 10 00 00    	mov    $0x100a,%edx
    3542:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    3548:	e8 e3 dd             	call   0x132e
    354b:	e8 30 dc             	call   0x117e
    354e:	be fb 49             	mov    $0x49fb,%si
    3551:	e8 a5 db             	call   0x10f9
    3554:	66 ba 09 10 00 00    	mov    $0x1009,%edx
    355a:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    3560:	e8 cb dd             	call   0x132e
    3563:	e8 18 dc             	call   0x117e
    3566:	be d8 51             	mov    $0x51d8,%si
    3569:	e8 8d db             	call   0x10f9
    356c:	66 ba 08 10 00 00    	mov    $0x1008,%edx
    3572:	66 26 03 96 e4 02    	add    %es:0x2e4(%bp),%edx
    3578:	e8 b3 dd             	call   0x132e
    357b:	e8 00 dc             	call   0x117e
    357e:	be 42 46             	mov    $0x4642,%si
    3581:	e8 75 db             	call   0x10f9
    3584:	be 4f 1a             	mov    $0x1a4f,%si
    3587:	e9 63 fe             	jmp    0x33ed
    358a:	3c a0                	cmp    $0xa0,%al
    358c:	0f 85 6f fe          	jne    0x33ff
    3590:	b0 00                	mov    $0x0,%al
    3592:	e9 5d fe             	jmp    0x33f2
    3595:	e8 f3 db             	call   0x118b
    3598:	3c 01                	cmp    $0x1,%al
    359a:	2e c6 04 20          	movb   $0x20,%cs:(%si)
    359e:	74 04                	je     0x35a4
    35a0:	2e c6 04 73          	movb   $0x73,%cs:(%si)
    35a4:	c3                   	ret    
    35a5:	57                   	push   %di
    35a6:	51                   	push   %cx
    35a7:	b8 00 40             	mov    $0x4000,%ax
    35aa:	8e e0                	mov    %ax,%fs
    35ac:	33 ff                	xor    %di,%di
    35ae:	b9 00 08             	mov    $0x800,%cx
    35b1:	64 83 3d 00          	cmpw   $0x0,%fs:(%di)
    35b5:	75 1a                	jne    0x35d1
    35b7:	83 c7 02             	add    $0x2,%di
    35ba:	e2 f5                	loop   0x35b1
    35bc:	b9 00 10             	mov    $0x1000,%cx
    35bf:	33 ff                	xor    %di,%di
    35c1:	64 88 05             	mov    %al,%fs:(%di)
    35c4:	40                   	inc    %ax
    35c5:	47                   	inc    %di
    35c6:	e2 f9                	loop   0x35c1
    35c8:	8c e0                	mov    %fs,%ax
    35ca:	66 c1 e0 10          	shl    $0x10,%eax
    35ce:	59                   	pop    %cx
    35cf:	5f                   	pop    %di
    35d0:	c3                   	ret    
    35d1:	8c e0                	mov    %fs,%ax
    35d3:	05 00 01             	add    $0x100,%ax
    35d6:	3d 00 80             	cmp    $0x8000,%ax
    35d9:	72 cf                	jb     0x35aa
    35db:	56                   	push   %si
    35dc:	be b0 46             	mov    $0x46b0,%si
    35df:	e8 17 db             	call   0x10f9
    35e2:	5e                   	pop    %si
    35e3:	b8 00 70             	mov    $0x7000,%ax
    35e6:	8e e0                	mov    %ax,%fs
    35e8:	eb d2                	jmp    0x35bc
    35ea:	57                   	push   %di
    35eb:	8b f8                	mov    %ax,%di
    35ed:	66 c1 e8 10          	shr    $0x10,%eax
    35f1:	8e e0                	mov    %ax,%fs
    35f3:	b9 00 10             	mov    $0x1000,%cx
    35f6:	64 c6 05 00          	movb   $0x0,%fs:(%di)
    35fa:	47                   	inc    %di
    35fb:	e2 f9                	loop   0x35f6
    35fd:	5f                   	pop    %di
    35fe:	c3                   	ret    
    35ff:	66 26 c7 86 d0 02 00 	movl   $0x0,%es:0x2d0(%bp)
    3606:	00 00 00 
    3609:	66 26 c7 86 d4 02 00 	movl   $0x0,%es:0x2d4(%bp)
    3610:	00 00 00 
    3613:	66 26 c7 86 d8 02 00 	movl   $0x0,%es:0x2d8(%bp)
    361a:	00 00 00 
    361d:	66 26 c7 86 dc 02 00 	movl   $0x0,%es:0x2dc(%bp)
    3624:	00 00 00 
    3627:	e8 7b ff             	call   0x35a5
    362a:	66 a3 98 54          	mov    %eax,0x5498
    362e:	8b 16 9a 54          	mov    0x549a,%dx
    3632:	e8 46 da             	call   0x107b
    3635:	66 26 89 86 d8 02    	mov    %eax,%es:0x2d8(%bp)
    363b:	26 c6 86 d0 02 1c    	movb   $0x1c,%es:0x2d0(%bp)
    3641:	e8 3d d7             	call   0xd81
    3644:	0f 85 c4 02          	jne    0x390c
    3648:	0f b5 3e 98 54       	lgs    0x5498,%di
    364d:	65 8a 05             	mov    %gs:(%di),%al
    3650:	be 90 50             	mov    $0x5090,%si
    3653:	3c 02                	cmp    $0x2,%al
    3655:	74 3f                	je     0x3696
    3657:	be 99 50             	mov    $0x5099,%si
    365a:	3c 01                	cmp    $0x1,%al
    365c:	74 38                	je     0x3696
    365e:	be a4 50             	mov    $0x50a4,%si
    3661:	3c 10                	cmp    $0x10,%al
    3663:	74 31                	je     0x3696
    3665:	be ad 50             	mov    $0x50ad,%si
    3668:	3c 11                	cmp    $0x11,%al
    366a:	74 2a                	je     0x3696
    366c:	be b6 50             	mov    $0x50b6,%si
    366f:	3c 12                	cmp    $0x12,%al
    3671:	74 23                	je     0x3696
    3673:	be bf 50             	mov    $0x50bf,%si
    3676:	3c 13                	cmp    $0x13,%al
    3678:	74 1c                	je     0x3696
    367a:	be c8 50             	mov    $0x50c8,%si
    367d:	3c 14                	cmp    $0x14,%al
    367f:	74 15                	je     0x3696
    3681:	be de 50             	mov    $0x50de,%si
    3684:	3c 15                	cmp    $0x15,%al
    3686:	74 0e                	je     0x3696
    3688:	be d3 50             	mov    $0x50d3,%si
    368b:	3c 16                	cmp    $0x16,%al
    368d:	74 07                	je     0x3696
    368f:	be e8 50             	mov    $0x50e8,%si
    3692:	3c 20                	cmp    $0x20,%al
    3694:	74 00                	je     0x3696
    3696:	57                   	push   %di
    3697:	26 0f be 86 e2 02    	movsbw %es:0x2e2(%bp),%ax
    369d:	8b f8                	mov    %ax,%di
    369f:	c1 e7 06             	shl    $0x6,%di
    36a2:	81 c7 f0 1c          	add    $0x1cf0,%di
    36a6:	e8 8b da             	call   0x1134
    36a9:	c6 05 2e             	movb   $0x2e,(%di)
    36ac:	47                   	inc    %di
    36ad:	c6 05 20             	movb   $0x20,(%di)
    36b0:	47                   	inc    %di
    36b1:	e8 36 da             	call   0x10ea
    36b4:	5f                   	pop    %di
    36b5:	e8 53 da             	call   0x110b
    36b8:	e8 3e da             	call   0x10f9
    36bb:	65 8a 45 04          	mov    %gs:0x4(%di),%al
    36bf:	be f1 50             	mov    $0x50f1,%si
    36c2:	e8 34 da             	call   0x10f9
    36c5:	e8 c3 da             	call   0x118b
    36c8:	e8 c0 d9             	call   0x108b
    36cb:	65 8a 45 05          	mov    %gs:0x5(%di),%al
    36cf:	e8 ae da             	call   0x1180
    36d2:	b0 2d                	mov    $0x2d,%al
    36d4:	e8 b6 d9             	call   0x108d
    36d7:	65 8a 45 07          	mov    %gs:0x7(%di),%al
    36db:	e8 af d9             	call   0x108d
    36de:	b0 2d                	mov    $0x2d,%al
    36e0:	e8 aa d9             	call   0x108d
    36e3:	65 8a 45 06          	mov    %gs:0x6(%di),%al
    36e7:	e8 96 da             	call   0x1180
    36ea:	65 8b 45 70          	mov    %gs:0x70(%di),%ax
    36ee:	0b c0                	or     %ax,%ax
    36f0:	74 1c                	je     0x370e
    36f2:	be 1e 52             	mov    $0x521e,%si
    36f5:	e8 01 da             	call   0x10f9
    36f8:	0a e4                	or     %ah,%ah
    36fa:	74 05                	je     0x3701
    36fc:	8a c4                	mov    %ah,%al
    36fe:	e8 7f da             	call   0x1180
    3701:	65 8b 45 70          	mov    %gs:0x70(%di),%ax
    3705:	e8 78 da             	call   0x1180
    3708:	be 26 52             	mov    $0x5226,%si
    370b:	e8 eb d9             	call   0x10f9
    370e:	be 65 53             	mov    $0x5365,%si
    3711:	e8 e5 d9             	call   0x10f9
    3714:	66 26 8b 86 e4 02    	mov    %es:0x2e4(%bp),%eax
    371a:	e8 68 e2             	call   0x1985
    371d:	26 8a 86 eb 02       	mov    %es:0x2eb(%bp),%al
    3722:	be 7c 53             	mov    $0x537c,%si
    3725:	e8 d1 d9             	call   0x10f9
    3728:	e8 60 da             	call   0x118b
    372b:	26 8a 86 ea 02       	mov    %es:0x2ea(%bp),%al
    3730:	c0 e8 03             	shr    $0x3,%al
    3733:	be 82 53             	mov    $0x5382,%si
    3736:	e8 c0 d9             	call   0x10f9
    3739:	e8 4f da             	call   0x118b
    373c:	26 8a 86 ea 02       	mov    %es:0x2ea(%bp),%al
    3741:	24 07                	and    $0x7,%al
    3743:	be 8d 53             	mov    $0x538d,%si
    3746:	e8 b0 d9             	call   0x10f9
    3749:	e8 3f da             	call   0x118b
    374c:	26 0f be b6 e2 02    	movsbw %es:0x2e2(%bp),%si
    3752:	8a 84 90 01          	mov    0x190(%si),%al
    3756:	be 98 53             	mov    $0x5398,%si
    3759:	e8 9d d9             	call   0x10f9
    375c:	e8 2c da             	call   0x118b
    375f:	65 8b 45 1a          	mov    %gs:0x1a(%di),%ax
    3763:	c1 e8 04             	shr    $0x4,%ax
    3766:	be ff 4a             	mov    $0x4aff,%si
    3769:	e8 8d d9             	call   0x10f9
    376c:	e8 1c da             	call   0x118b
    376f:	be 12 4b             	mov    $0x4b12,%si
    3772:	e8 84 d9             	call   0x10f9
    3775:	65 8a 45 28          	mov    %gs:0x28(%di),%al
    3779:	24 07                	and    $0x7,%al
    377b:	be 32 4b             	mov    $0x4b32,%si
    377e:	3c 01                	cmp    $0x1,%al
    3780:	74 0e                	je     0x3790
    3782:	be 38 4b             	mov    $0x4b38,%si
    3785:	3c 02                	cmp    $0x2,%al
    3787:	74 07                	je     0x3790
    3789:	be 6b 4b             	mov    $0x4b6b,%si
    378c:	3c 00                	cmp    $0x0,%al
    378e:	74 00                	je     0x3790
    3790:	e8 66 d9             	call   0x10f9
    3793:	65 8a 45 28          	mov    %gs:0x28(%di),%al
    3797:	c0 e8 03             	shr    $0x3,%al
    379a:	24 07                	and    $0x7,%al
    379c:	3c 01                	cmp    $0x1,%al
    379e:	be 40 4b             	mov    $0x4b40,%si
    37a1:	74 08                	je     0x37ab
    37a3:	be 65 4b             	mov    $0x4b65,%si
    37a6:	7f 03                	jg     0x37ab
    37a8:	be 49 4b             	mov    $0x4b49,%si
    37ab:	e8 4b d9             	call   0x10f9
    37ae:	26 c6 86 d0 02 53    	movb   $0x53,%es:0x2d0(%bp)
    37b4:	e8 ca d5             	call   0xd81
    37b7:	0f 85 51 01          	jne    0x390c
    37bb:	65 81 bd 84 00 40 1f 	cmpw   $0x1f40,%gs:0x84(%di)
    37c2:	76 0b                	jbe    0x37cf
    37c4:	83 0e 72 54 01       	orw    $0x1,0x5472
    37c9:	be 61 4a             	mov    $0x4a61,%si
    37cc:	e8 2a d9             	call   0x10f9
    37cf:	65 8a 85 90 00       	mov    %gs:0x90(%di),%al
    37d4:	0a c0                	or     %al,%al
    37d6:	74 17                	je     0x37ef
    37d8:	83 0e 72 54 01       	orw    $0x1,0x5472
    37dd:	be c3 4a             	mov    $0x4ac3,%si
    37e0:	e8 16 d9             	call   0x10f9
    37e3:	be dd 4a             	mov    $0x4add,%si
    37e6:	e8 ac fd             	call   0x3595
    37e9:	be d0 4a             	mov    $0x4ad0,%si
    37ec:	e8 0a d9             	call   0x10f9
    37ef:	65 8a 85 8c 00       	mov    %gs:0x8c(%di),%al
    37f4:	0a c0                	or     %al,%al
    37f6:	74 17                	je     0x380f
    37f8:	83 0e 72 54 01       	orw    $0x1,0x5472
    37fd:	be c3 4a             	mov    $0x4ac3,%si
    3800:	e8 f6 d8             	call   0x10f9
    3803:	be f5 4a             	mov    $0x4af5,%si
    3806:	e8 8c fd             	call   0x3595
    3809:	be e8 4a             	mov    $0x4ae8,%si
    380c:	e8 ea d8             	call   0x10f9
    380f:	65 8a 85 94 00       	mov    %gs:0x94(%di),%al
    3814:	0a c0                	or     %al,%al
    3816:	74 45                	je     0x385d
    3818:	83 0e 72 54 01       	orw    $0x1,0x5472
    381d:	be 99 4b             	mov    $0x4b99,%si
    3820:	e8 75 fd             	call   0x3598
    3823:	be 7d 4b             	mov    $0x4b7d,%si
    3826:	e8 d0 d8             	call   0x10f9
    3829:	8d 9d 98 00          	lea    0x98(%di),%bx
    382d:	0f b6 c8             	movzbw %al,%cx
    3830:	65 8a 47 01          	mov    %gs:0x1(%bx),%al
    3834:	e8 47 d9             	call   0x117e
    3837:	b0 3a                	mov    $0x3a,%al
    3839:	e8 51 d8             	call   0x108d
    383c:	65 8a 07             	mov    %gs:(%bx),%al
    383f:	e8 3c d9             	call   0x117e
    3842:	b0 20                	mov    $0x20,%al
    3844:	e8 46 d8             	call   0x108d
    3847:	83 c3 02             	add    $0x2,%bx
    384a:	e2 e4                	loop   0x3830
    384c:	65 80 bd 94 00 01    	cmpb   $0x1,%gs:0x94(%di)
    3852:	be 43 46             	mov    $0x4643,%si
    3855:	74 03                	je     0x385a
    3857:	be 44 46             	mov    $0x4644,%si
    385a:	e8 9c d8             	call   0x10f9
    385d:	65 8a 05             	mov    %gs:(%di),%al
    3860:	a2 58 54             	mov    %al,0x5458
    3863:	26 c6 86 d0 02 3d    	movb   $0x3d,%es:0x2d0(%bp)
    3869:	e8 15 d5             	call   0xd81
    386c:	74 0d                	je     0x387b
    386e:	26 c6 86 d0 02 3c    	movb   $0x3c,%es:0x2d0(%bp)
    3874:	e8 0a d5             	call   0xd81
    3877:	0f 85 91 00          	jne    0x390c
    387b:	65 8a 45 01          	mov    %gs:0x1(%di),%al
    387f:	24 20                	and    $0x20,%al
    3881:	08 06 5b 54          	or     %al,0x545b
    3885:	26 80 be e2 02 00    	cmpb   $0x0,%es:0x2e2(%bp)
    388b:	0f 84 80 00          	je     0x390f
    388f:	a0 56 01             	mov    0x156,%al
    3892:	65 3a 45 34          	cmp    %gs:0x34(%di),%al
    3896:	74 0f                	je     0x38a7
    3898:	65 88 45 34          	mov    %al,%gs:0x34(%di)
    389c:	26 c6 86 d0 02 3c    	movb   $0x3c,%es:0x2d0(%bp)
    38a2:	e8 dc d4             	call   0xd81
    38a5:	75 65                	jne    0x390c
    38a7:	26 80 be e2 02 00    	cmpb   $0x0,%es:0x2e2(%bp)
    38ad:	75 3e                	jne    0x38ed
    38af:	be cb 4e             	mov    $0x4ecb,%si
    38b2:	e8 44 d8             	call   0x10f9
    38b5:	f6 06 56 01 01       	testb  $0x1,0x156
    38ba:	be 14 4e             	mov    $0x4e14,%si
    38bd:	75 1d                	jne    0x38dc
    38bf:	be 31 4e             	mov    $0x4e31,%si
    38c2:	c7 06 f6 1b 20 7f    	movw   $0x7f20,0x1bf6
    38c8:	a0 56 01             	mov    0x156,%al
    38cb:	24 60                	and    $0x60,%al
    38cd:	3c 20                	cmp    $0x20,%al
    38cf:	75 0b                	jne    0x38dc
    38d1:	c7 06 f6 1b 3f fe    	movw   $0xfe3f,0x1bf6
    38d7:	c6 06 3b 4e 38       	movb   $0x38,0x4e3b
    38dc:	e8 1a d8             	call   0x10f9
    38df:	bb 5a 00             	mov    $0x5a,%bx
    38e2:	e8 e4 d8             	call   0x11c9
    38e5:	3d 00 32             	cmp    $0x3200,%ax
    38e8:	75 03                	jne    0x38ed
    38ea:	e8 db 07             	call   0x40c8
    38ed:	e8 58 d5             	call   0xe48
    38f0:	f6 06 56 01 02       	testb  $0x2,0x156
    38f5:	74 0a                	je     0x3901
    38f7:	f6 06 56 01 01       	testb  $0x1,0x156
    38fc:	75 03                	jne    0x3901
    38fe:	e8 a7 01             	call   0x3aa8
    3901:	f8                   	clc    
    3902:	9c                   	pushf  
    3903:	66 a1 98 54          	mov    0x5498,%eax
    3907:	e8 e0 fc             	call   0x35ea
    390a:	9d                   	popf   
    390b:	c3                   	ret    
    390c:	f9                   	stc    
    390d:	eb f3                	jmp    0x3902
    390f:	65 8a 45 34          	mov    %gs:0x34(%di),%al
    3913:	a2 56 01             	mov    %al,0x156
    3916:	eb 8f                	jmp    0x38a7
    3918:	66 53                	push   %ebx
    391a:	66 0f b7 d8          	movzwl %ax,%ebx
    391e:	fa                   	cli    
    391f:	8e 26 00 1c          	mov    0x1c00,%fs
    3923:	66 64 a1 6c 00       	mov    %fs:0x6c,%eax
    3928:	fb                   	sti    
    3929:	e8 05 00             	call   0x3931
    392c:	77 fb                	ja     0x3929
    392e:	66 5b                	pop    %ebx
    3930:	c3                   	ret    
    3931:	66 50                	push   %eax
    3933:	66 53                	push   %ebx
    3935:	8e 26 00 1c          	mov    0x1c00,%fs
    3939:	66 64 8b 1e 6c 00    	mov    %fs:0x6c,%ebx
    393f:	66 2b d8             	sub    %eax,%ebx
    3942:	66 58                	pop    %eax
    3944:	66 50                	push   %eax
    3946:	66 0f b7 c0          	movzwl %ax,%eax
    394a:	66 3b c3             	cmp    %ebx,%eax
    394d:	66 5b                	pop    %ebx
    394f:	66 58                	pop    %eax
    3951:	c3                   	ret    
    3952:	be ff ff             	mov    $0xffff,%si
    3955:	46                   	inc    %si
    3956:	80 3e 55 01 10       	cmpb   $0x10,0x155
    395b:	0f 83 d1 00          	jae    0x3a30
    395f:	b9 10 00             	mov    $0x10,%cx
    3962:	ba 69 10             	mov    $0x1069,%dx
    3965:	b8 02 b1             	mov    $0xb102,%ax
    3968:	cd 1a                	int    $0x1a
    396a:	0f 82 c2 00          	jb     0x3a30
    396e:	e8 17 01             	call   0x3a88
    3971:	0f b6 3e 55 01       	movzbw 0x155,%di
    3976:	d1 e7                	shl    %di
    3978:	89 9d a0 00          	mov    %bx,0xa0(%di)
    397c:	d1 e7                	shl    %di
    397e:	66 a1 c0 54          	mov    0x54c0,%eax
    3982:	66 83 e0 f0          	and    $0xfffffff0,%eax
    3986:	66 89 85 10 01       	mov    %eax,0x110(%di)
    398b:	c1 ef 02             	shr    $0x2,%di
    398e:	0f b6 0e ec 54       	movzbw 0x54ec,%cx
    3993:	88 8d 90 01          	mov    %cl,0x190(%di)
    3997:	80 f9 10             	cmp    $0x10,%cl
    399a:	73 53                	jae    0x39ef
    399c:	ba 01 00             	mov    $0x1,%dx
    399f:	d3 e2                	shl    %cl,%dx
    39a1:	85 16 70 54          	test   %dx,0x5470
    39a5:	75 48                	jne    0x39ef
    39a7:	09 16 70 54          	or     %dx,0x5470
    39ab:	bf 20 00             	mov    $0x20,%di
    39ae:	f7 d2                	not    %dx
    39b0:	80 f9 08             	cmp    $0x8,%cl
    39b3:	72 08                	jb     0x39bd
    39b5:	80 e9 08             	sub    $0x8,%cl
    39b8:	b2 fb                	mov    $0xfb,%dl
    39ba:	bf c0 01             	mov    $0x1c0,%di
    39bd:	c0 e1 02             	shl    $0x2,%cl
    39c0:	03 f9                	add    %cx,%di
    39c2:	56                   	push   %si
    39c3:	0f b6 36 55 01       	movzbw 0x155,%si
    39c8:	d1 e6                	shl    %si
    39ca:	88 b4 f0 00          	mov    %dh,0xf0(%si)
    39ce:	88 94 f1 00          	mov    %dl,0xf1(%si)
    39d2:	d1 e6                	shl    %si
    39d4:	8e 26 02 1c          	mov    0x1c02,%fs
    39d8:	66 64 8b 05          	mov    %fs:(%di),%eax
    39dc:	66 89 84 40 00       	mov    %eax,0x40(%si)
    39e1:	d1 ee                	shr    %si
    39e3:	8b 84 74 54          	mov    0x5474(%si),%ax
    39e7:	64 89 05             	mov    %ax,%fs:(%di)
    39ea:	64 8c 4d 02          	mov    %cs,%fs:0x2(%di)
    39ee:	5e                   	pop    %si
    39ef:	fe 06 55 01          	incb   0x155
    39f3:	8a 0e b4 54          	mov    0x54b4,%cl
    39f7:	80 c9 04             	or     $0x4,%cl
    39fa:	bf 04 00             	mov    $0x4,%di
    39fd:	b8 0b b1             	mov    $0xb10b,%ax
    3a00:	cd 1a                	int    $0x1a
    3a02:	53                   	push   %bx
    3a03:	83 e3 f8             	and    $0xfff8,%bx
    3a06:	bf 04 00             	mov    $0x4,%di
    3a09:	b8 08 b1             	mov    $0xb108,%ax
    3a0c:	cd 1a                	int    $0x1a
    3a0e:	80 c9 04             	or     $0x4,%cl
    3a11:	bf 04 00             	mov    $0x4,%di
    3a14:	b8 0b b1             	mov    $0xb10b,%ax
    3a17:	cd 1a                	int    $0x1a
    3a19:	5b                   	pop    %bx
    3a1a:	80 3e bd 54 00       	cmpb   $0x0,0x54bd
    3a1f:	0f 85 32 ff          	jne    0x3955
    3a23:	b1 08                	mov    $0x8,%cl
    3a25:	bf 0d 00             	mov    $0xd,%di
    3a28:	b8 0b b1             	mov    $0xb10b,%ax
    3a2b:	cd 1a                	int    $0x1a
    3a2d:	e9 25 ff             	jmp    0x3955
    3a30:	0f b6 06 55 01       	movzbw 0x155,%ax
    3a35:	0b c0                	or     %ax,%ax
    3a37:	c3                   	ret    
    3a38:	26 8b 9e ea 02       	mov    %es:0x2ea(%bp),%bx
    3a3d:	88 3e 57 54          	mov    %bh,0x5457
    3a41:	0a ff                	or     %bh,%bh
    3a43:	74 42                	je     0x3a87
    3a45:	fe cf                	dec    %bh
    3a47:	b3 00                	mov    $0x0,%bl
    3a49:	bf 0b 00             	mov    $0xb,%di
    3a4c:	b8 08 b1             	mov    $0xb108,%ax
    3a4f:	cd 1a                	int    $0x1a
    3a51:	72 05                	jb     0x3a58
    3a53:	80 f9 06             	cmp    $0x6,%cl
    3a56:	74 07                	je     0x3a5f
    3a58:	80 c3 08             	add    $0x8,%bl
    3a5b:	75 ec                	jne    0x3a49
    3a5d:	eb e2                	jmp    0x3a41
    3a5f:	bf 19 00             	mov    $0x19,%di
    3a62:	b8 08 b1             	mov    $0xb108,%ax
    3a65:	cd 1a                	int    $0x1a
    3a67:	72 ef                	jb     0x3a58
    3a69:	3a 0e 57 54          	cmp    0x5457,%cl
    3a6d:	75 e9                	jne    0x3a58
    3a6f:	bf 1b 00             	mov    $0x1b,%di
    3a72:	b8 08 b1             	mov    $0xb108,%ax
    3a75:	cd 1a                	int    $0x1a
    3a77:	72 0e                	jb     0x3a87
    3a79:	0a c9                	or     %cl,%cl
    3a7b:	75 0a                	jne    0x3a87
    3a7d:	b1 08                	mov    $0x8,%cl
    3a7f:	bf 1b 00             	mov    $0x1b,%di
    3a82:	b8 0b b1             	mov    $0xb10b,%ax
    3a85:	cd 1a                	int    $0x1a
    3a87:	c3                   	ret    
    3a88:	b8 0a b1             	mov    $0xb10a,%ax
    3a8b:	b9 10 00             	mov    $0x10,%cx
    3a8e:	33 ff                	xor    %di,%di
    3a90:	51                   	push   %cx
    3a91:	66 8b 8d b0 54       	mov    0x54b0(%di),%ecx
    3a96:	50                   	push   %ax
    3a97:	cd 1a                	int    $0x1a
    3a99:	58                   	pop    %ax
    3a9a:	66 89 8d b0 54       	mov    %ecx,0x54b0(%di)
    3a9f:	59                   	pop    %cx
    3aa0:	72 05                	jb     0x3aa7
    3aa2:	83 c7 04             	add    $0x4,%di
    3aa5:	e2 e9                	loop   0x3a90
    3aa7:	c3                   	ret    
    3aa8:	60                   	pusha  
    3aa9:	a0 e3 1b             	mov    0x1be3,%al
    3aac:	0a 06 e4 1b          	or     0x1be4,%al
    3ab0:	0f 85 64 01          	jne    0x3c18
    3ab4:	be 98 51             	mov    $0x5198,%si
    3ab7:	e8 3f d6             	call   0x10f9
    3aba:	26 c6 86 d0 02 04    	movb   $0x4,%es:0x2d0(%bp)
    3ac0:	66 26 8b 86 d8 02    	mov    %es:0x2d8(%bp),%eax
    3ac6:	66 83 c0 58          	add    $0x58,%eax
    3aca:	66 65 89 45 04       	mov    %eax,%gs:0x4(%di)
    3acf:	65 c6 45 01 a1       	movb   $0xa1,%gs:0x1(%di)
    3ad4:	c6 06 e5 1b ff       	movb   $0xff,0x1be5
    3ad9:	fe 06 e5 1b          	incb   0x1be5
    3add:	80 3e e5 1b 30       	cmpb   $0x30,0x1be5
    3ae2:	0f 83 32 01          	jae    0x3c18
    3ae6:	66 65 c7 45 0a 00 00 	movl   $0x0,%gs:0xa(%di)
    3aed:	00 00 
    3aef:	66 65 c7 45 0e 00 00 	movl   $0x0,%gs:0xe(%di)
    3af6:	00 00 
    3af8:	66 65 c7 45 12 00 00 	movl   $0x0,%gs:0x12(%di)
    3aff:	00 00 
    3b01:	a0 e5 1b             	mov    0x1be5,%al
    3b04:	65 88 05             	mov    %al,%gs:(%di)
    3b07:	65 c7 45 02 24 00    	movw   $0x24,%gs:0x2(%di)
    3b0d:	65 c6 45 08 06       	movb   $0x6,%gs:0x8(%di)
    3b12:	65 c6 45 0a 12       	movb   $0x12,%gs:0xa(%di)
    3b17:	65 c6 45 0e 24       	movb   $0x24,%gs:0xe(%di)
    3b1c:	e8 62 d2             	call   0xd81
    3b1f:	75 b8                	jne    0x3ad9
    3b21:	65 8a 45 58          	mov    %gs:0x58(%di),%al
    3b25:	24 1f                	and    $0x1f,%al
    3b27:	3c 05                	cmp    $0x5,%al
    3b29:	75 ae                	jne    0x3ad9
    3b2b:	a0 e5 1b             	mov    0x1be5,%al
    3b2e:	c0 e8 04             	shr    $0x4,%al
    3b31:	be b7 51             	mov    $0x51b7,%si
    3b34:	e8 c2 d5             	call   0x10f9
    3b37:	e8 51 d6             	call   0x118b
    3b3a:	a0 e5 1b             	mov    0x1be5,%al
    3b3d:	24 0f                	and    $0xf,%al
    3b3f:	be d8 51             	mov    $0x51d8,%si
    3b42:	e8 b4 d5             	call   0x10f9
    3b45:	e8 43 d6             	call   0x118b
    3b48:	b0 20                	mov    $0x20,%al
    3b4a:	e8 40 d5             	call   0x108d
    3b4d:	8d 75 60             	lea    0x60(%di),%si
    3b50:	b9 1c 00             	mov    $0x1c,%cx
    3b53:	65 8a 04             	mov    %gs:(%si),%al
    3b56:	e8 34 d5             	call   0x108d
    3b59:	46                   	inc    %si
    3b5a:	e2 f7                	loop   0x3b53
    3b5c:	66 65 c7 45 0a 00 00 	movl   $0x0,%gs:0xa(%di)
    3b63:	00 00 
    3b65:	66 65 c7 45 0e 00 00 	movl   $0x0,%gs:0xe(%di)
    3b6c:	00 00 
    3b6e:	66 65 c7 45 12 00 00 	movl   $0x0,%gs:0x12(%di)
    3b75:	00 00 
    3b77:	65 c7 45 02 08 00    	movw   $0x8,%gs:0x2(%di)
    3b7d:	65 c6 45 08 0a       	movb   $0xa,%gs:0x8(%di)
    3b82:	65 c6 45 0a 25       	movb   $0x25,%gs:0xa(%di)
    3b87:	e8 f7 d1             	call   0xd81
    3b8a:	0f 85 4b ff          	jne    0x3ad9
    3b8e:	66 65 8b 45 5c       	mov    %gs:0x5c(%di),%eax
    3b93:	e8 cf d4             	call   0x1065
    3b96:	66 3d 00 08 00 00    	cmp    $0x800,%eax
    3b9c:	0f 85 39 ff          	jne    0x3ad9
    3ba0:	66 65 8b 45 58       	mov    %gs:0x58(%di),%eax
    3ba5:	e8 bd d4             	call   0x1065
    3ba8:	66 40                	inc    %eax
    3baa:	66 a3 10 1c          	mov    %eax,0x1c10
    3bae:	e8 69 00             	call   0x3c1a
    3bb1:	0f 82 24 ff          	jb     0x3ad9
    3bb5:	66 a1 0c 1c          	mov    0x1c0c,%eax
    3bb9:	e8 db 02             	call   0x3e97
    3bbc:	0f 85 19 ff          	jne    0x3ad9
    3bc0:	26 8a 86 e2 02       	mov    %es:0x2e2(%bp),%al
    3bc5:	a2 e6 1b             	mov    %al,0x1be6
    3bc8:	80 3e e3 1b 00       	cmpb   $0x0,0x1be3
    3bcd:	75 49                	jne    0x3c18
    3bcf:	80 3e e7 1b 00       	cmpb   $0x0,0x1be7
    3bd4:	74 3d                	je     0x3c13
    3bd6:	8d b5 16 02          	lea    0x216(%di),%si
    3bda:	b9 04 00             	mov    $0x4,%cx
    3bdd:	65 80 3c 80          	cmpb   $0x80,%gs:(%si)
    3be1:	74 14                	je     0x3bf7
    3be3:	83 c6 10             	add    $0x10,%si
    3be6:	e2 f5                	loop   0x3bdd
    3be8:	be cd 4b             	mov    $0x4bcd,%si
    3beb:	e8 0b d5             	call   0x10f9
    3bee:	b8 32 01             	mov    $0x132,%ax
    3bf1:	e8 24 fd             	call   0x3918
    3bf4:	e9 e2 fe             	jmp    0x3ad9
    3bf7:	65 8a 44 05          	mov    %gs:0x5(%si),%al
    3bfb:	a2 f9 1b             	mov    %al,0x1bf9
    3bfe:	65 8a 44 06          	mov    %gs:0x6(%si),%al
    3c02:	8a e0                	mov    %al,%ah
    3c04:	24 3f                	and    $0x3f,%al
    3c06:	a2 f8 1b             	mov    %al,0x1bf8
    3c09:	c0 ec 06             	shr    $0x6,%ah
    3c0c:	65 8a 44 07          	mov    %gs:0x7(%si),%al
    3c10:	a3 fa 1b             	mov    %ax,0x1bfa
    3c13:	c6 06 e4 1b 01       	movb   $0x1,0x1be4
    3c18:	61                   	popa   
    3c19:	c3                   	ret    
    3c1a:	66 b8 11 00 00 00    	mov    $0x11,%eax
    3c20:	e8 74 02             	call   0x3e97
    3c23:	75 63                	jne    0x3c88
    3c25:	65 80 7d 58 00       	cmpb   $0x0,%gs:0x58(%di)
    3c2a:	75 5c                	jne    0x3c88
    3c2c:	66 65 8b 85 9f 00    	mov    %gs:0x9f(%di),%eax
    3c32:	e8 62 02             	call   0x3e97
    3c35:	75 51                	jne    0x3c88
    3c37:	65 80 7d 58 01       	cmpb   $0x1,%gs:0x58(%di)
    3c3c:	75 4a                	jne    0x3c88
    3c3e:	65 80 7d 59 00       	cmpb   $0x0,%gs:0x59(%di)
    3c43:	75 43                	jne    0x3c88
    3c45:	65 80 7d 78 88       	cmpb   $0x88,%gs:0x78(%di)
    3c4a:	75 3c                	jne    0x3c88
    3c4c:	be cf 4f             	mov    $0x4fcf,%si
    3c4f:	e8 a7 d4             	call   0x10f9
    3c52:	65 8a 85 98 00       	mov    %gs:0x98(%di),%al
    3c57:	0a c0                	or     %al,%al
    3c59:	be 19 50             	mov    $0x5019,%si
    3c5c:	74 03                	je     0x3c61
    3c5e:	be ed 4f             	mov    $0x4fed,%si
    3c61:	e8 95 d4             	call   0x10f9
    3c64:	0a c0                	or     %al,%al
    3c66:	be 3f 50             	mov    $0x503f,%si
    3c69:	74 03                	je     0x3c6e
    3c6b:	be 3c 50             	mov    $0x503c,%si
    3c6e:	e8 88 d4             	call   0x10f9
    3c71:	c6 06 59 54 01       	movb   $0x1,0x5459
    3c76:	8d 75 78             	lea    0x78(%di),%si
    3c79:	89 36 9c 54          	mov    %si,0x549c
    3c7d:	0a c0                	or     %al,%al
    3c7f:	75 46                	jne    0x3cc7
    3c81:	e8 5f 01             	call   0x3de3
    3c84:	0f 83 f0 00          	jae    0x3d78
    3c88:	f9                   	stc    
    3c89:	c3                   	ret    
    3c8a:	60                   	pusha  
    3c8b:	0f b6 3e 59 54       	movzbw 0x5459,%di
    3c90:	d1 e7                	shl    %di
    3c92:	89 b5 9c 54          	mov    %si,0x549c(%di)
    3c96:	8b f8                	mov    %ax,%di
    3c98:	fe 06 59 54          	incb   0x5459
    3c9c:	a0 59 54             	mov    0x5459,%al
    3c9f:	e8 e9 d4             	call   0x118b
    3ca2:	e8 e6 d3             	call   0x108b
    3ca5:	b0 20                	mov    $0x20,%al
    3ca7:	e8 e3 d3             	call   0x108d
    3caa:	b9 13 00             	mov    $0x13,%cx
    3cad:	65 8a 05             	mov    %gs:(%di),%al
    3cb0:	47                   	inc    %di
    3cb1:	0a c0                	or     %al,%al
    3cb3:	74 03                	je     0x3cb8
    3cb5:	e8 d5 d3             	call   0x108d
    3cb8:	e2 f3                	loop   0x3cad
    3cba:	0b d2                	or     %dx,%dx
    3cbc:	74 05                	je     0x3cc3
    3cbe:	8b f2                	mov    %dx,%si
    3cc0:	e8 36 d4             	call   0x10f9
    3cc3:	61                   	popa   
    3cc4:	e9 44 d4             	jmp    0x110b
    3cc7:	8d b5 98 00          	lea    0x98(%di),%si
    3ccb:	8d 44 04             	lea    0x4(%si),%ax
    3cce:	33 d2                	xor    %dx,%dx
    3cd0:	e8 b7 ff             	call   0x3c8a
    3cd3:	65 8b 4c 02          	mov    %gs:0x2(%si),%cx
    3cd7:	41                   	inc    %cx
    3cd8:	b8 20 00             	mov    $0x20,%ax
    3cdb:	f7 e1                	mul    %cx
    3cdd:	03 f0                	add    %ax,%si
    3cdf:	65 80 3c 90          	cmpb   $0x90,%gs:(%si)
    3ce3:	74 e6                	je     0x3ccb
    3ce5:	8d 44 04             	lea    0x4(%si),%ax
    3ce8:	33 d2                	xor    %dx,%dx
    3cea:	e8 9d ff             	call   0x3c8a
    3ced:	a0 59 54             	mov    0x5459,%al
    3cf0:	be 67 4f             	mov    $0x4f67,%si
    3cf3:	e8 03 d4             	call   0x10f9
    3cf6:	e8 92 d4             	call   0x118b
    3cf9:	be 73 4f             	mov    $0x4f73,%si
    3cfc:	e8 fa d3             	call   0x10f9
    3cff:	e8 ec d4             	call   0x11ee
    3d02:	2c 31                	sub    $0x31,%al
    3d04:	74 61                	je     0x3d67
    3d06:	3a 06 59 54          	cmp    0x5459,%al
    3d0a:	73 f3                	jae    0x3cff
    3d0c:	be a8 4f             	mov    $0x4fa8,%si
    3d0f:	e8 e7 d3             	call   0x10f9
    3d12:	c6 06 59 54 00       	movb   $0x0,0x5459
    3d17:	0f b6 f0             	movzbw %al,%si
    3d1a:	d1 e6                	shl    %si
    3d1c:	8b b4 9c 54          	mov    0x549c(%si),%si
    3d20:	65 8b 4c 02          	mov    %gs:0x2(%si),%cx
    3d24:	83 c6 20             	add    $0x20,%si
    3d27:	65 80 3c 44          	cmpb   $0x44,%gs:(%si)
    3d2b:	74 14                	je     0x3d41
    3d2d:	65 0f b6 5c 01       	movzbw %gs:0x1(%si),%bx
    3d32:	83 e3 0f             	and    $0xf,%bx
    3d35:	d1 e3                	shl    %bx
    3d37:	8b 97 37 54          	mov    0x5437(%bx),%dx
    3d3b:	8d 44 0d             	lea    0xd(%si),%ax
    3d3e:	e8 49 ff             	call   0x3c8a
    3d41:	e2 e1                	loop   0x3d24
    3d43:	a0 59 54             	mov    0x5459,%al
    3d46:	be 77 4f             	mov    $0x4f77,%si
    3d49:	e8 ad d3             	call   0x10f9
    3d4c:	e8 3c d4             	call   0x118b
    3d4f:	be 83 4f             	mov    $0x4f83,%si
    3d52:	e8 a4 d3             	call   0x10f9
    3d55:	e8 96 d4             	call   0x11ee
    3d58:	3d 1b 01             	cmp    $0x11b,%ax
    3d5b:	0f 84 f3 fe          	je     0x3c52
    3d5f:	2c 31                	sub    $0x31,%al
    3d61:	3a 06 59 54          	cmp    0x5459,%al
    3d65:	73 ee                	jae    0x3d55
    3d67:	e8 a1 d3             	call   0x110b
    3d6a:	0f b6 f0             	movzbw %al,%si
    3d6d:	d1 e6                	shl    %si
    3d6f:	8b b4 9c 54          	mov    0x549c(%si),%si
    3d73:	e8 6d 00             	call   0x3de3
    3d76:	72 cb                	jb     0x3d43
    3d78:	66 65 8b 44 08       	mov    %gs:0x8(%si),%eax
    3d7d:	66 a3 0c 1c          	mov    %eax,0x1c0c
    3d81:	65 8b 44 02          	mov    %gs:0x2(%si),%ax
    3d85:	0b c0                	or     %ax,%ax
    3d87:	75 03                	jne    0x3d8c
    3d89:	b8 c0 07             	mov    $0x7c0,%ax
    3d8c:	66 c1 e0 10          	shl    $0x10,%eax
    3d90:	66 a3 08 1c          	mov    %eax,0x1c08
    3d94:	65 8b 44 06          	mov    %gs:0x6(%si),%ax
    3d98:	c1 e8 02             	shr    $0x2,%ax
    3d9b:	75 01                	jne    0x3d9e
    3d9d:	40                   	inc    %ax
    3d9e:	a3 fc 1b             	mov    %ax,0x1bfc
    3da1:	be 9e 53             	mov    $0x539e,%si
    3da4:	e8 52 d3             	call   0x10f9
    3da7:	bb 7e 00             	mov    $0x7e,%bx
    3daa:	e8 1c d4             	call   0x11c9
    3dad:	3d 79 15             	cmp    $0x1579,%ax
    3db0:	75 12                	jne    0x3dc4
    3db2:	be ca 53             	mov    $0x53ca,%si
    3db5:	e8 41 d3             	call   0x10f9
    3db8:	c6 06 e3 1b 00       	movb   $0x0,0x1be3
    3dbd:	c6 06 e4 1b 00       	movb   $0x0,0x1be4
    3dc2:	f9                   	stc    
    3dc3:	c3                   	ret    
    3dc4:	80 3e e7 1b 00       	cmpb   $0x0,0x1be7
    3dc9:	75 10                	jne    0x3ddb
    3dcb:	8e 26 00 1c          	mov    0x1c00,%fs
    3dcf:	64 83 0e 8f 00 40    	orw    $0x40,%fs:0x8f
    3dd5:	64 83 0e 10 00 40    	orw    $0x40,%fs:0x10
    3ddb:	be ec 4e             	mov    $0x4eec,%si
    3dde:	e8 18 d3             	call   0x10f9
    3de1:	f8                   	clc    
    3de2:	c3                   	ret    
    3de3:	65 8a 44 01          	mov    %gs:0x1(%si),%al
    3de7:	24 0f                	and    $0xf,%al
    3de9:	0f 84 9a 00          	je     0x3e87
    3ded:	c6 06 0b 4f 43       	movb   $0x43,0x4f0b
    3df2:	c6 06 e7 1b 80       	movb   $0x80,0x1be7
    3df7:	3c 04                	cmp    $0x4,%al
    3df9:	0f 84 89 00          	je     0x3e86
    3dfd:	c6 06 0b 4f 41       	movb   $0x41,0x4f0b
    3e02:	c6 06 e7 1b 00       	movb   $0x0,0x1be7
    3e07:	c6 06 f9 1b 01       	movb   $0x1,0x1bf9
    3e0c:	c6 06 f8 1b 0f       	movb   $0xf,0x1bf8
    3e11:	c6 06 ee 1b 0f       	movb   $0xf,0x1bee
    3e16:	c7 06 fa 1b 4f 00    	movw   $0x4f,0x1bfa
    3e1c:	66 c7 06 14 1c 60 09 	movl   $0x960,0x1c14
    3e23:	00 00 
    3e25:	c6 06 e8 1b 02       	movb   $0x2,0x1be8
    3e2a:	c6 06 ef 1b 2a       	movb   $0x2a,0x1bef
    3e2f:	c6 06 f1 1b 50       	movb   $0x50,0x1bf1
    3e34:	3c 01                	cmp    $0x1,%al
    3e36:	74 4e                	je     0x3e86
    3e38:	c6 06 f8 1b 12       	movb   $0x12,0x1bf8
    3e3d:	c6 06 ee 1b 12       	movb   $0x12,0x1bee
    3e42:	66 c7 06 14 1c 40 0b 	movl   $0xb40,0x1c14
    3e49:	00 00 
    3e4b:	c6 06 e8 1b 04       	movb   $0x4,0x1be8
    3e50:	c6 06 ef 1b 1b       	movb   $0x1b,0x1bef
    3e55:	c6 06 f1 1b 6c       	movb   $0x6c,0x1bf1
    3e5a:	3c 02                	cmp    $0x2,%al
    3e5c:	74 28                	je     0x3e86
    3e5e:	c6 06 f8 1b 24       	movb   $0x24,0x1bf8
    3e63:	66 c7 06 14 1c 80 16 	movl   $0x1680,0x1c14
    3e6a:	00 00 
    3e6c:	c6 06 e8 1b 06       	movb   $0x6,0x1be8
    3e71:	3c 03                	cmp    $0x3,%al
    3e73:	74 11                	je     0x3e86
    3e75:	65 8a 44 01          	mov    %gs:0x1(%si),%al
    3e79:	e8 8f d2             	call   0x110b
    3e7c:	e8 a3 d2             	call   0x1122
    3e7f:	be 44 4f             	mov    $0x4f44,%si
    3e82:	e8 74 d2             	call   0x10f9
    3e85:	f9                   	stc    
    3e86:	c3                   	ret    
    3e87:	c6 06 0b 4f 52       	movb   $0x52,0x4f0b
    3e8c:	c6 06 e3 1b 01       	movb   $0x1,0x1be3
    3e91:	c6 06 e7 1b 8f       	movb   $0x8f,0x1be7
    3e96:	c3                   	ret    
    3e97:	66 65 c7 45 0a 00 00 	movl   $0x0,%gs:0xa(%di)
    3e9e:	00 00 
    3ea0:	66 65 c7 45 0e 00 00 	movl   $0x0,%gs:0xe(%di)
    3ea7:	00 00 
    3ea9:	66 65 c7 45 12 00 00 	movl   $0x0,%gs:0x12(%di)
    3eb0:	00 00 
    3eb2:	65 c7 45 02 00 08    	movw   $0x800,%gs:0x2(%di)
    3eb8:	65 c6 45 08 0a       	movb   $0xa,%gs:0x8(%di)
    3ebd:	65 c6 45 0a 28       	movb   $0x28,%gs:0xa(%di)
    3ec2:	e8 a0 d1             	call   0x1065
    3ec5:	66 65 89 45 0c       	mov    %eax,%gs:0xc(%di)
    3eca:	65 c6 45 12 01       	movb   $0x1,%gs:0x12(%di)
    3ecf:	e9 af ce             	jmp    0xd81
    3ed2:	fa                   	cli    
    3ed3:	b8 00 c0             	mov    $0xc000,%ax
    3ed6:	cd 15                	int    $0x15
    3ed8:	72 71                	jb     0x3f4b
    3eda:	26 f6 47 05 04       	testb  $0x4,%es:0x5(%bx)
    3edf:	74 6a                	je     0x3f4b
    3ee1:	8e 26 00 1c          	mov    0x1c00,%fs
    3ee5:	64 8e 06 0e 00       	mov    %fs:0xe,%es
    3eea:	64 a1 13 00          	mov    %fs:0x13,%ax
    3eee:	c1 e0 06             	shl    $0x6,%ax
    3ef1:	26 0f b6 0e 00 00    	movzbw %es:0x0,%cx
    3ef7:	8c c2                	mov    %es,%dx
    3ef9:	3b c2                	cmp    %dx,%ax
    3efb:	64 a1 13 00          	mov    %fs:0x13,%ax
    3eff:	74 02                	je     0x3f03
    3f01:	2b c1                	sub    %cx,%ax
    3f03:	83 e8 02             	sub    $0x2,%ax
    3f06:	64 a3 13 00          	mov    %ax,%fs:0x13
    3f0a:	c1 e0 06             	shl    $0x6,%ax
    3f0d:	64 a3 0e 00          	mov    %ax,%fs:0xe
    3f11:	8e e0                	mov    %ax,%fs
    3f13:	8b c1                	mov    %cx,%ax
    3f15:	c1 e0 06             	shl    $0x6,%ax
    3f18:	a3 fe 1b             	mov    %ax,0x1bfe
    3f1b:	c1 e1 0a             	shl    $0xa,%cx
    3f1e:	33 ff                	xor    %di,%di
    3f20:	26 8a 05             	mov    %es:(%di),%al
    3f23:	64 88 05             	mov    %al,%fs:(%di)
    3f26:	47                   	inc    %di
    3f27:	e2 f7                	loop   0x3f20
    3f29:	64 80 06 00 00 02    	addb   $0x2,%fs:0x0
    3f2f:	a1 fe 1b             	mov    0x1bfe,%ax
    3f32:	2e 8e 26 00 1c       	mov    %cs:0x1c00,%fs
    3f37:	64 03 06 0e 00       	add    %fs:0xe,%ax
    3f3c:	8e e0                	mov    %ax,%fs
    3f3e:	33 ff                	xor    %di,%di
    3f40:	b9 00 08             	mov    $0x800,%cx
    3f43:	33 c0                	xor    %ax,%ax
    3f45:	64 88 05             	mov    %al,%fs:(%di)
    3f48:	e2 fb                	loop   0x3f45
    3f4a:	c3                   	ret    
    3f4b:	c6 06 e9 1b 01       	movb   $0x1,0x1be9
    3f50:	f6 06 56 01 01       	testb  $0x1,0x156
    3f55:	75 f3                	jne    0x3f4a
    3f57:	0f b6 0e 55 01       	movzbw 0x155,%cx
    3f5c:	33 f6                	xor    %si,%si
    3f5e:	8e 26 00 1c          	mov    0x1c00,%fs
    3f62:	8a 84 d1 00          	mov    0xd1(%si),%al
    3f66:	c6 84 d1 00 00       	movb   $0x0,0xd1(%si)
    3f6b:	64 28 06 75 00       	sub    %al,%fs:0x75
    3f70:	46                   	inc    %si
    3f71:	e2 ef                	loop   0x3f62
    3f73:	80 0e 56 01 01       	orb    $0x1,0x156
    3f78:	be 51 50             	mov    $0x5051,%si
    3f7b:	e8 7b d1             	call   0x10f9
    3f7e:	b8 7e 00             	mov    $0x7e,%ax
    3f81:	e9 94 f9             	jmp    0x3918
    3f84:	24 50                	and    $0x50,%al
    3f86:	6e                   	outsb  %ds:(%si),(%dx)
    3f87:	50                   	push   %ax
    3f88:	00 66 60             	add    %ah,0x60(%bp)
    3f8b:	bb c0 1c             	mov    $0x1cc0,%bx
    3f8e:	89 1e 1a 00          	mov    %bx,0x1a
    3f92:	be 84 3f             	mov    $0x3f84,%si
    3f95:	8d 3f                	lea    (%bx),%di
    3f97:	e8 50 d1             	call   0x10ea
    3f9a:	c6 47 04 01          	movb   $0x1,0x4(%bx)
    3f9e:	c6 47 05 02          	movb   $0x2,0x5(%bx)
    3fa2:	c6 47 14 02          	movb   $0x2,0x14(%bx)
    3fa6:	c7 47 16 b8 1c       	movw   $0x1cb8,0x16(%bx)
    3fab:	8d 47 20             	lea    0x20(%bx),%ax
    3fae:	89 47 0e             	mov    %ax,0xe(%bx)
    3fb1:	8d 47 30             	lea    0x30(%bx),%ax
    3fb4:	89 47 10             	mov    %ax,0x10(%bx)
    3fb7:	8d 7f 20             	lea    0x20(%bx),%di
    3fba:	be 45 46             	mov    $0x4645,%si
    3fbd:	e8 2a d1             	call   0x10ea
    3fc0:	c6 47 09 00          	movb   $0x0,0x9(%bx)
    3fc4:	80 7f 70 00          	cmpb   $0x0,0x70(%bx)
    3fc8:	74 06                	je     0x3fd0
    3fca:	8d 47 40             	lea    0x40(%bx),%ax
    3fcd:	89 47 06             	mov    %ax,0x6(%bx)
    3fd0:	b9 20 00             	mov    $0x20,%cx
    3fd3:	8b fb                	mov    %bx,%di
    3fd5:	33 c0                	xor    %ax,%ax
    3fd7:	02 05                	add    (%di),%al
    3fd9:	47                   	inc    %di
    3fda:	e2 fb                	loop   0x3fd7
    3fdc:	f6 d0                	not    %al
    3fde:	fe c0                	inc    %al
    3fe0:	88 47 09             	mov    %al,0x9(%bx)
    3fe3:	8b 47 06             	mov    0x6(%bx),%ax
    3fe6:	83 c3 40             	add    $0x40,%bx
    3fe9:	0b c0                	or     %ax,%ax
    3feb:	75 a5                	jne    0x3f92
    3fed:	66 61                	popal  
    3fef:	c3                   	ret    
    3ff0:	26 c6 44 02 19       	movb   $0x19,%es:0x2(%si)
    3ff5:	26 c6 44 03 50       	movb   $0x50,%es:0x3(%si)
    3ffa:	26 c6 04 00          	movb   $0x0,%es:(%si)
    3ffe:	26 c6 44 01 00       	movb   $0x0,%es:0x1(%si)
    4003:	26 c6 44 05 10       	movb   $0x10,%es:0x5(%si)
    4008:	26 c6 44 04 b1       	movb   $0xb1,%es:0x4(%si)
    400d:	eb 26                	jmp    0x4035
    400f:	26 8a 44 05          	mov    %es:0x5(%si),%al
    4013:	26 c6 44 05 00       	movb   $0x0,%es:0x5(%si)
    4018:	26 c6 44 04 20       	movb   $0x20,%es:0x4(%si)
    401d:	e8 15 00             	call   0x4035
    4020:	26 88 44 05          	mov    %al,%es:0x5(%si)
    4024:	e8 06 00             	call   0x402d
    4027:	e8 88 04             	call   0x44b2
    402a:	e9 ee 04             	jmp    0x451b
    402d:	26 fe 0c             	decb   %es:(%si)
    4030:	26 80 6c 01 02       	subb   $0x2,%es:0x1(%si)
    4035:	60                   	pusha  
    4036:	8e 26 6c 54          	mov    0x546c,%fs
    403a:	b0 50                	mov    $0x50,%al
    403c:	26 f6 24             	mulb   %es:(%si)
    403f:	26 0f b6 7c 01       	movzbw %es:0x1(%si),%di
    4044:	03 f8                	add    %ax,%di
    4046:	d1 e7                	shl    %di
    4048:	03 3e 6e 54          	add    0x546e,%di
    404c:	26 8a 44 04          	mov    %es:0x4(%si),%al
    4050:	26 8a 64 05          	mov    %es:0x5(%si),%ah
    4054:	26 0f b6 4c 02       	movzbw %es:0x2(%si),%cx
    4059:	51                   	push   %cx
    405a:	26 0f b6 4c 03       	movzbw %es:0x3(%si),%cx
    405f:	64 89 05             	mov    %ax,%fs:(%di)
    4062:	83 c7 02             	add    $0x2,%di
    4065:	e2 f8                	loop   0x405f
    4067:	b9 50 00             	mov    $0x50,%cx
    406a:	26 2a 4c 03          	sub    %es:0x3(%si),%cl
    406e:	d1 e1                	shl    %cx
    4070:	03 f9                	add    %cx,%di
    4072:	59                   	pop    %cx
    4073:	e2 e4                	loop   0x4059
    4075:	61                   	popa   
    4076:	c3                   	ret    
    4077:	60                   	pusha  
    4078:	b4 0f                	mov    $0xf,%ah
    407a:	cd 10                	int    $0x10
    407c:	32 db                	xor    %bl,%bl
    407e:	c1 e3 04             	shl    $0x4,%bx
    4081:	89 1e 6e 54          	mov    %bx,0x546e
    4085:	3c 07                	cmp    $0x7,%al
    4087:	c7 06 6c 54 00 b0    	movw   $0xb000,0x546c
    408d:	74 2e                	je     0x40bd
    408f:	c7 06 6c 54 00 b8    	movw   $0xb800,0x546c
    4095:	b8 00 1b             	mov    $0x1b00,%ax
    4098:	cd 10                	int    $0x10
    409a:	3c 1b                	cmp    $0x1b,%al
    409c:	74 21                	je     0x40bf
    409e:	8e 26 00 1c          	mov    0x1c00,%fs
    40a2:	64 f6 06 87 00 ff    	testb  $0xff,%fs:0x87
    40a8:	75 15                	jne    0x40bf
    40aa:	64 8b 16 63 00       	mov    %fs:0x63,%dx
    40af:	83 c2 04             	add    $0x4,%dx
    40b2:	64 a0 65 00          	mov    %fs:0x65,%al
    40b6:	24 df                	and    $0xdf,%al
    40b8:	ee                   	out    %al,(%dx)
    40b9:	64 a2 65 00          	mov    %al,%fs:0x65
    40bd:	61                   	popa   
    40be:	c3                   	ret    
    40bf:	b8 03 10             	mov    $0x1003,%ax
    40c2:	32 db                	xor    %bl,%bl
    40c4:	cd 10                	int    $0x10
    40c6:	eb f5                	jmp    0x40bd
    40c8:	26 c6 86 d0 02 2b    	movb   $0x2b,%es:0x2d0(%bp)
    40ce:	26 c6 86 d2 02 02    	movb   $0x2,%es:0x2d2(%bp)
    40d4:	e8 aa cc             	call   0xd81
    40d7:	75 21                	jne    0x40fa
    40d9:	8d 75 20             	lea    0x20(%di),%si
    40dc:	b9 05 00             	mov    $0x5,%cx
    40df:	65 80 7c 08 04       	cmpb   $0x4,%gs:0x8(%si)
    40e4:	75 0f                	jne    0x40f5
    40e6:	66 65 83 7c 04 00    	cmpl   $0x0,%gs:0x4(%si)
    40ec:	74 07                	je     0x40f5
    40ee:	c6 06 e0 1b 01       	movb   $0x1,0x1be0
    40f3:	eb 05                	jmp    0x40fa
    40f5:	83 c6 40             	add    $0x40,%si
    40f8:	e2 e5                	loop   0x40df
    40fa:	b4 01                	mov    $0x1,%ah
    40fc:	b5 20                	mov    $0x20,%ch
    40fe:	cd 10                	int    $0x10
    4100:	a0 56 01             	mov    0x156,%al
    4103:	a2 df 1b             	mov    %al,0x1bdf
    4106:	b8 00 0f             	mov    $0xf00,%ax
    4109:	8e c0                	mov    %ax,%es
    410b:	e8 69 ff             	call   0x4077
    410e:	be 50 00             	mov    $0x50,%si
    4111:	e8 dc fe             	call   0x3ff0
    4114:	26 c6 04 0b          	movb   $0xb,%es:(%si)
    4118:	26 c6 44 01 1c       	movb   $0x1c,%es:0x1(%si)
    411d:	26 c6 44 02 15       	movb   $0x15,%es:0x2(%si)
    4122:	26 c6 44 03 04       	movb   $0x4,%es:0x3(%si)
    4127:	80 3e e0 1b 01       	cmpb   $0x1,0x1be0
    412c:	26 c6 44 03 03       	movb   $0x3,%es:0x3(%si)
    4131:	26 c6 44 04 00       	movb   $0x0,%es:0x4(%si)
    4136:	26 c6 44 05 3f       	movb   $0x3f,%es:0x5(%si)
    413b:	26 c6 44 06 f3       	movb   $0xf3,%es:0x6(%si)
    4140:	26 c7 44 10 19 43    	movw   $0x4319,%es:0x10(%si)
    4146:	26 c7 44 12 09 43    	movw   $0x4309,%es:0x12(%si)
    414c:	26 c7 44 14 a5 42    	movw   $0x42a5,%es:0x14(%si)
    4152:	26 c7 44 16 b5 45    	movw   $0x45b5,%es:0x16(%si)
    4158:	e8 c3 01             	call   0x431e
    415b:	e8 b5 00             	call   0x4213
    415e:	be 00 00             	mov    $0x0,%si
    4161:	26 c6 44 02 04       	movb   $0x4,%es:0x2(%si)
    4166:	26 c6 44 03 1d       	movb   $0x1d,%es:0x3(%si)
    416b:	26 c6 04 14          	movb   $0x14,%es:(%si)
    416f:	26 c6 44 01 1a       	movb   $0x1a,%es:0x1(%si)
    4174:	26 c6 44 05 3f       	movb   $0x3f,%es:0x5(%si)
    4179:	e8 93 fe             	call   0x400f
    417c:	26 c7 44 0c 5e 4c    	movw   $0x4c5e,%es:0xc(%si)
    4182:	e8 d5 03             	call   0x455a
    4185:	26 fe 44 08          	incb   %es:0x8(%si)
    4189:	26 83 44 0c 1b       	addw   $0x1b,%es:0xc(%si)
    418e:	e8 c9 03             	call   0x455a
    4191:	26 c6 44 02 01       	movb   $0x1,%es:0x2(%si)
    4196:	26 c6 44 03 50       	movb   $0x50,%es:0x3(%si)
    419b:	26 c6 04 18          	movb   $0x18,%es:(%si)
    419f:	26 c6 44 01 00       	movb   $0x0,%es:0x1(%si)
    41a4:	26 c6 44 05 10       	movb   $0x10,%es:0x5(%si)
    41a9:	26 c6 44 04 b1       	movb   $0xb1,%es:0x4(%si)
    41ae:	e8 84 fe             	call   0x4035
    41b1:	e8 3a d0             	call   0x11ee
    41b4:	e8 0c 00             	call   0x41c3
    41b7:	c4 2e 94 54          	les    0x5494,%bp
    41bb:	b0 08                	mov    $0x8,%al
    41bd:	e8 57 d3             	call   0x1517
    41c0:	e9 bf cd             	jmp    0xf82
    41c3:	06                   	push   %es
    41c4:	55                   	push   %bp
    41c5:	57                   	push   %di
    41c6:	c4 2e 94 54          	les    0x5494,%bp
    41ca:	a0 56 01             	mov    0x156,%al
    41cd:	3a 06 df 1b          	cmp    0x1bdf,%al
    41d1:	74 20                	je     0x41f3
    41d3:	26 c6 86 d0 02 3d    	movb   $0x3d,%es:0x2d0(%bp)
    41d9:	e8 a5 cb             	call   0xd81
    41dc:	75 15                	jne    0x41f3
    41de:	a0 56 01             	mov    0x156,%al
    41e1:	0f b4 3e 98 54       	lfs    0x5498,%di
    41e6:	64 88 45 34          	mov    %al,%fs:0x34(%di)
    41ea:	26 c6 86 d0 02 3c    	movb   $0x3c,%es:0x2d0(%bp)
    41f0:	e8 8e cb             	call   0xd81
    41f3:	5f                   	pop    %di
    41f4:	5d                   	pop    %bp
    41f5:	07                   	pop    %es
    41f6:	c3                   	ret    
    41f7:	60                   	pusha  
    41f8:	be 00 00             	mov    $0x0,%si
    41fb:	e8 b7 03             	call   0x45b5
    41fe:	61                   	popa   
    41ff:	eb 12                	jmp    0x4213
    4201:	26 0f b6 5c 04       	movzbw %es:0x4(%si),%bx
    4206:	d1 e3                	shl    %bx
    4208:	03 de                	add    %si,%bx
    420a:	60                   	pusha  
    420b:	be 00 00             	mov    $0x0,%si
    420e:	26 ff 57 10          	call   *%es:0x10(%bx)
    4212:	61                   	popa   
    4213:	be 50 00             	mov    $0x50,%si
    4216:	26 8a 04             	mov    %es:(%si),%al
    4219:	26 88 44 08          	mov    %al,%es:0x8(%si)
    421d:	26 8a 44 01          	mov    %es:0x1(%si),%al
    4221:	26 88 44 09          	mov    %al,%es:0x9(%si)
    4225:	26 8a 44 05          	mov    %es:0x5(%si),%al
    4229:	26 88 44 0b          	mov    %al,%es:0xb(%si)
    422d:	26 8a 44 02          	mov    %es:0x2(%si),%al
    4231:	26 88 44 0a          	mov    %al,%es:0xa(%si)
    4235:	26 0f b6 4c 03       	movzbw %es:0x3(%si),%cx
    423a:	e8 4c 03             	call   0x4589
    423d:	26 fe 44 08          	incb   %es:0x8(%si)
    4241:	e2 f7                	loop   0x423a
    4243:	26 8a 44 04          	mov    %es:0x4(%si),%al
    4247:	26 02 04             	add    %es:(%si),%al
    424a:	26 88 44 08          	mov    %al,%es:0x8(%si)
    424e:	26 8a 44 06          	mov    %es:0x6(%si),%al
    4252:	26 88 44 0b          	mov    %al,%es:0xb(%si)
    4256:	e8 30 03             	call   0x4589
    4259:	e8 92 cf             	call   0x11ee
    425c:	80 3e e0 1b 00       	cmpb   $0x0,0x1be0
    4261:	74 05                	je     0x4268
    4263:	3d 00 13             	cmp    $0x1300,%ax
    4266:	74 8f                	je     0x41f7
    4268:	80 fc 50             	cmp    $0x50,%ah
    426b:	74 0e                	je     0x427b
    426d:	80 fc 48             	cmp    $0x48,%ah
    4270:	74 1e                	je     0x4290
    4272:	3c 0d                	cmp    $0xd,%al
    4274:	74 8b                	je     0x4201
    4276:	3c 1b                	cmp    $0x1b,%al
    4278:	75 99                	jne    0x4213
    427a:	c3                   	ret    
    427b:	26 fe 44 04          	incb   %es:0x4(%si)
    427f:	26 8a 44 04          	mov    %es:0x4(%si),%al
    4283:	26 3a 44 03          	cmp    %es:0x3(%si),%al
    4287:	72 8a                	jb     0x4213
    4289:	26 c6 44 04 00       	movb   $0x0,%es:0x4(%si)
    428e:	eb 83                	jmp    0x4213
    4290:	26 8a 44 04          	mov    %es:0x4(%si),%al
    4294:	0a c0                	or     %al,%al
    4296:	75 04                	jne    0x429c
    4298:	26 8a 44 03          	mov    %es:0x3(%si),%al
    429c:	fe c8                	dec    %al
    429e:	26 88 44 04          	mov    %al,%es:0x4(%si)
    42a2:	e9 6e ff             	jmp    0x4213
    42a5:	26 c6 44 02 07       	movb   $0x7,%es:0x2(%si)
    42aa:	26 c6 44 03 27       	movb   $0x27,%es:0x3(%si)
    42af:	26 c6 04 0e          	movb   $0xe,%es:(%si)
    42b3:	26 c6 44 01 27       	movb   $0x27,%es:0x1(%si)
    42b8:	26 c6 44 05 cf       	movb   $0xcf,%es:0x5(%si)
    42bd:	e8 4f fd             	call   0x400f
    42c0:	26 c7 44 0c 46 4d    	movw   $0x4d46,%es:0xc(%si)
    42c6:	b9 05 00             	mov    $0x5,%cx
    42c9:	e8 8e 02             	call   0x455a
    42cc:	26 fe 44 08          	incb   %es:0x8(%si)
    42d0:	26 83 44 0c 26       	addw   $0x26,%es:0xc(%si)
    42d5:	e2 f2                	loop   0x42c9
    42d7:	26 fe 4c 09          	decb   %es:0x9(%si)
    42db:	e8 33 02             	call   0x4511
    42de:	26 c7 44 0c 10 4e    	movw   $0x4e10,%es:0xc(%si)
    42e4:	e8 73 02             	call   0x455a
    42e7:	26 80 44 09 26       	addb   $0x26,%es:0x9(%si)
    42ec:	26 c7 44 0c 12 4e    	movw   $0x4e12,%es:0xc(%si)
    42f2:	e8 65 02             	call   0x455a
    42f5:	e8 f6 ce             	call   0x11ee
    42f8:	3d 6e 31             	cmp    $0x316e,%ax
    42fb:	74 21                	je     0x431e
    42fd:	3d 79 15             	cmp    $0x1579,%ax
    4300:	75 f3                	jne    0x42f5
    4302:	80 36 56 01 20       	xorb   $0x20,0x156
    4307:	eb 15                	jmp    0x431e
    4309:	f6 06 56 01 01       	testb  $0x1,0x156
    430e:	0f 85 43 01          	jne    0x4455
    4312:	80 36 56 01 02       	xorb   $0x2,0x156
    4317:	eb 05                	jmp    0x431e
    4319:	80 36 56 01 01       	xorb   $0x1,0x156
    431e:	60                   	pusha  
    431f:	be 10 00             	mov    $0x10,%si
    4322:	e8 cb fc             	call   0x3ff0
    4325:	26 c6 44 02 07       	movb   $0x7,%es:0x2(%si)
    432a:	26 c6 44 03 17       	movb   $0x17,%es:0x3(%si)
    432f:	26 c6 04 09          	movb   $0x9,%es:(%si)
    4333:	26 c6 44 01 1d       	movb   $0x1d,%es:0x1(%si)
    4338:	26 c6 44 05 00       	movb   $0x0,%es:0x5(%si)
    433d:	26 c6 44 04 20       	movb   $0x20,%es:0x4(%si)
    4342:	e8 f0 fc             	call   0x4035
    4345:	26 c6 44 05 3f       	movb   $0x3f,%es:0x5(%si)
    434a:	e8 e0 fc             	call   0x402d
    434d:	e8 cb 01             	call   0x451b
    4350:	26 80 44 09 05       	addb   $0x5,%es:0x9(%si)
    4355:	26 c6 44 0a 30       	movb   $0x30,%es:0xa(%si)
    435a:	26 c7 44 0c fa 4c    	movw   $0x4cfa,%es:0xc(%si)
    4360:	e8 f7 01             	call   0x455a
    4363:	26 fe 44 08          	incb   %es:0x8(%si)
    4367:	e8 ca 01             	call   0x4534
    436a:	26 c6 44 0a 3f       	movb   $0x3f,%es:0xa(%si)
    436f:	26 c7 44 0c 2e 4d    	movw   $0x4d2e,%es:0xc(%si)
    4375:	e8 e2 01             	call   0x455a
    4378:	bf 50 00             	mov    $0x50,%di
    437b:	26 c6 45 05 3f       	movb   $0x3f,%es:0x5(%di)
    4380:	26 c6 45 06 f3       	movb   $0xf3,%es:0x6(%di)
    4385:	f6 06 56 01 01       	testb  $0x1,0x156
    438a:	26 c7 44 0c f1 4b    	movw   $0x4bf1,%es:0xc(%si)
    4390:	74 06                	je     0x4398
    4392:	26 c7 44 0c e3 4b    	movw   $0x4be3,%es:0xc(%si)
    4398:	e8 80 01             	call   0x451b
    439b:	26 80 44 08 02       	addb   $0x2,%es:0x8(%si)
    43a0:	e8 b7 01             	call   0x455a
    43a3:	f6 06 56 01 02       	testb  $0x2,0x156
    43a8:	26 c7 44 0c 13 4c    	movw   $0x4c13,%es:0xc(%si)
    43ae:	75 06                	jne    0x43b6
    43b0:	26 c7 44 0c fe 4b    	movw   $0x4bfe,%es:0xc(%si)
    43b6:	26 fe 44 08          	incb   %es:0x8(%si)
    43ba:	e8 9d 01             	call   0x455a
    43bd:	f6 06 56 01 20       	testb  $0x20,0x156
    43c2:	26 c7 44 0c 3b 4c    	movw   $0x4c3b,%es:0xc(%si)
    43c8:	75 06                	jne    0x43d0
    43ca:	26 c7 44 0c 27 4c    	movw   $0x4c27,%es:0xc(%si)
    43d0:	26 fe 44 08          	incb   %es:0x8(%si)
    43d4:	e8 83 01             	call   0x455a
    43d7:	26 fe 44 08          	incb   %es:0x8(%si)
    43db:	80 3e e0 1b 01       	cmpb   $0x1,0x1be0
    43e0:	75 00                	jne    0x43e2
    43e2:	26 c6 44 02 01       	movb   $0x1,%es:0x2(%si)
    43e7:	26 c6 44 03 50       	movb   $0x50,%es:0x3(%si)
    43ec:	26 c6 04 18          	movb   $0x18,%es:(%si)
    43f0:	26 c6 44 01 00       	movb   $0x0,%es:0x1(%si)
    43f5:	26 c6 44 05 3f       	movb   $0x3f,%es:0x5(%si)
    43fa:	e8 38 fc             	call   0x4035
    43fd:	e8 31 01             	call   0x4531
    4400:	26 c6 44 0a 3f       	movb   $0x3f,%es:0xa(%si)
    4405:	26 c7 44 0c 94 4c    	movw   $0x4c94,%es:0xc(%si)
    440b:	e8 4c 01             	call   0x455a
    440e:	26 c6 44 02 01       	movb   $0x1,%es:0x2(%si)
    4413:	26 c6 44 03 50       	movb   $0x50,%es:0x3(%si)
    4418:	26 c6 04 00          	movb   $0x0,%es:(%si)
    441c:	26 c6 44 01 00       	movb   $0x0,%es:0x1(%si)
    4421:	26 c6 44 05 3f       	movb   $0x3f,%es:0x5(%si)
    4426:	e8 0c fc             	call   0x4035
    4429:	26 c6 44 08 00       	movb   $0x0,%es:0x8(%si)
    442e:	26 c7 44 0c fc 45    	movw   $0x45fc,%es:0xc(%si)
    4434:	e8 23 01             	call   0x455a
    4437:	26 c6 44 09 0e       	movb   $0xe,%es:0x9(%si)
    443c:	26 c7 44 0c 70 01    	movw   $0x170,%es:0xc(%si)
    4442:	e8 15 01             	call   0x455a
    4445:	26 c6 44 09 3a       	movb   $0x3a,%es:0x9(%si)
    444a:	26 c7 44 0c 0b 46    	movw   $0x460b,%es:0xc(%si)
    4450:	e8 07 01             	call   0x455a
    4453:	61                   	popa   
    4454:	c3                   	ret    
    4455:	26 c6 44 02 03       	movb   $0x3,%es:0x2(%si)
    445a:	26 c6 44 03 17       	movb   $0x17,%es:0x3(%si)
    445f:	26 c6 04 14          	movb   $0x14,%es:(%si)
    4463:	26 c6 44 01 1d       	movb   $0x1d,%es:0x1(%si)
    4468:	26 c6 44 05 38       	movb   $0x38,%es:0x5(%si)
    446d:	e8 9f fb             	call   0x400f
    4470:	26 c7 44 0c e5 4c    	movw   $0x4ce5,%es:0xc(%si)
    4476:	e8 e1 00             	call   0x455a
    4479:	b8 12 00             	mov    $0x12,%ax
    447c:	e8 99 f4             	call   0x3918
    447f:	e9 9c fe             	jmp    0x431e
    4482:	26 0f b6 4c 03       	movzbw %es:0x3(%si),%cx
    4487:	80 e9 02             	sub    $0x2,%cl
    448a:	26 c7 44 0c 04 4e    	movw   $0x4e04,%es:0xc(%si)
    4490:	e8 c7 00             	call   0x455a
    4493:	26 fe 44 09          	incb   %es:0x9(%si)
    4497:	e2 f7                	loop   0x4490
    4499:	c3                   	ret    
    449a:	26 0f b6 4c 02       	movzbw %es:0x2(%si),%cx
    449f:	80 e9 02             	sub    $0x2,%cl
    44a2:	26 c7 44 0c 06 4e    	movw   $0x4e06,%es:0xc(%si)
    44a8:	e8 af 00             	call   0x455a
    44ab:	26 fe 44 08          	incb   %es:0x8(%si)
    44af:	e2 f7                	loop   0x44a8
    44b1:	c3                   	ret    
    44b2:	60                   	pusha  
    44b3:	26 8a 44 05          	mov    %es:0x5(%si),%al
    44b7:	26 88 44 0a          	mov    %al,%es:0xa(%si)
    44bb:	e8 6b 00             	call   0x4529
    44be:	e8 5d 00             	call   0x451e
    44c1:	e8 be ff             	call   0x4482
    44c4:	e8 76 00             	call   0x453d
    44c7:	e8 54 00             	call   0x451e
    44ca:	e8 b5 ff             	call   0x4482
    44cd:	e8 64 00             	call   0x4534
    44d0:	e8 3e 00             	call   0x4511
    44d3:	e8 c4 ff             	call   0x449a
    44d6:	e8 72 00             	call   0x454b
    44d9:	e8 35 00             	call   0x4511
    44dc:	e8 bb ff             	call   0x449a
    44df:	e8 4f 00             	call   0x4531
    44e2:	26 c7 44 0c 08 4e    	movw   $0x4e08,%es:0xc(%si)
    44e8:	e8 6f 00             	call   0x455a
    44eb:	e8 4f 00             	call   0x453d
    44ee:	26 c7 44 0c 0e 4e    	movw   $0x4e0e,%es:0xc(%si)
    44f4:	e8 63 00             	call   0x455a
    44f7:	e8 51 00             	call   0x454b
    44fa:	26 c7 44 0c 0c 4e    	movw   $0x4e0c,%es:0xc(%si)
    4500:	e8 57 00             	call   0x455a
    4503:	e8 23 00             	call   0x4529
    4506:	26 c7 44 0c 0a 4e    	movw   $0x4e0a,%es:0xc(%si)
    450c:	e8 4b 00             	call   0x455a
    450f:	61                   	popa   
    4510:	c3                   	ret    
    4511:	26 8a 04             	mov    %es:(%si),%al
    4514:	fe c0                	inc    %al
    4516:	26 88 44 08          	mov    %al,%es:0x8(%si)
    451a:	c3                   	ret    
    451b:	e8 f3 ff             	call   0x4511
    451e:	26 8a 44 01          	mov    %es:0x1(%si),%al
    4522:	fe c0                	inc    %al
    4524:	26 88 44 09          	mov    %al,%es:0x9(%si)
    4528:	c3                   	ret    
    4529:	26 8a 04             	mov    %es:(%si),%al
    452c:	26 88 44 08          	mov    %al,%es:0x8(%si)
    4530:	c3                   	ret    
    4531:	e8 f5 ff             	call   0x4529
    4534:	26 8a 44 01          	mov    %es:0x1(%si),%al
    4538:	26 88 44 09          	mov    %al,%es:0x9(%si)
    453c:	c3                   	ret    
    453d:	26 8a 04             	mov    %es:(%si),%al
    4540:	26 02 44 02          	add    %es:0x2(%si),%al
    4544:	fe c8                	dec    %al
    4546:	26 88 44 08          	mov    %al,%es:0x8(%si)
    454a:	c3                   	ret    
    454b:	26 8a 44 01          	mov    %es:0x1(%si),%al
    454f:	26 02 44 03          	add    %es:0x3(%si),%al
    4553:	fe c8                	dec    %al
    4555:	26 88 44 09          	mov    %al,%es:0x9(%si)
    4559:	c3                   	ret    
    455a:	60                   	pusha  
    455b:	26 8b 7c 0c          	mov    %es:0xc(%si),%di
    455f:	8e 26 6c 54          	mov    0x546c,%fs
    4563:	26 0f b6 5c 09       	movzbw %es:0x9(%si),%bx
    4568:	b0 50                	mov    $0x50,%al
    456a:	26 f6 64 08          	mulb   %es:0x8(%si)
    456e:	03 d8                	add    %ax,%bx
    4570:	d1 e3                	shl    %bx
    4572:	03 1e 6e 54          	add    0x546e,%bx
    4576:	26 8a 64 0a          	mov    %es:0xa(%si),%ah
    457a:	8a 05                	mov    (%di),%al
    457c:	0a c0                	or     %al,%al
    457e:	74 33                	je     0x45b3
    4580:	64 89 07             	mov    %ax,%fs:(%bx)
    4583:	83 c3 02             	add    $0x2,%bx
    4586:	47                   	inc    %di
    4587:	eb f1                	jmp    0x457a
    4589:	60                   	pusha  
    458a:	b0 50                	mov    $0x50,%al
    458c:	26 f6 64 08          	mulb   %es:0x8(%si)
    4590:	26 0f b6 5c 09       	movzbw %es:0x9(%si),%bx
    4595:	03 d8                	add    %ax,%bx
    4597:	d1 e3                	shl    %bx
    4599:	03 1e 6e 54          	add    0x546e,%bx
    459d:	26 0f b6 4c 0a       	movzbw %es:0xa(%si),%cx
    45a2:	26 8a 44 0b          	mov    %es:0xb(%si),%al
    45a6:	8e 26 6c 54          	mov    0x546c,%fs
    45aa:	64 88 47 01          	mov    %al,%fs:0x1(%bx)
    45ae:	83 c3 02             	add    $0x2,%bx
    45b1:	e2 f7                	loop   0x45aa
    45b3:	61                   	popa   
    45b4:	c3                   	ret    
    45b5:	66 60                	pushal 
    45b7:	0f a8                	push   %gs
    45b9:	0f a0                	push   %fs
    45bb:	06                   	push   %es
    45bc:	1e                   	push   %ds
    45bd:	e8 03 fc             	call   0x41c3
    45c0:	c4 2e 94 54          	les    0x5494,%bp
    45c4:	e8 e5 c8             	call   0xeac
    45c7:	1f                   	pop    %ds
    45c8:	07                   	pop    %es
    45c9:	0f a1                	pop    %fs
    45cb:	0f a9                	pop    %gs
    45cd:	66 61                	popal  
    45cf:	26 c6 44 02 03       	movb   $0x3,%es:0x2(%si)
    45d4:	26 c6 44 03 28       	movb   $0x28,%es:0x3(%si)
    45d9:	26 c6 04 14          	movb   $0x14,%es:(%si)
    45dd:	26 c6 44 01 1b       	movb   $0x1b,%es:0x1(%si)
    45e2:	26 c6 44 05 cf       	movb   $0xcf,%es:0x5(%si)
    45e7:	e8 25 fa             	call   0x400f
    45ea:	26 c7 44 0c 07 4d    	movw   $0x4d07,%es:0xc(%si)
    45f0:	e8 67 ff             	call   0x455a
    45f3:	bb 32 01             	mov    $0x132,%bx
    45f6:	e8 d0 cb             	call   0x11c9
    45f9:	e9 22 fd             	jmp    0x431e
    45fc:	20 44 41             	and    %al,0x41(%si)
    45ff:	43                   	inc    %bx
    4600:	39 36 30 20          	cmp    %si,0x2030
    4604:	42                   	inc    %dx
    4605:	49                   	dec    %cx
    4606:	4f                   	dec    %di
    4607:	53                   	push   %bx
    4608:	20 56 00             	and    %dl,0x0(%bp)
    460b:	5b                   	pop    %bx
    460c:	63 5d 20             	arpl   %bx,0x20(%di)
    460f:	4d                   	dec    %bp
    4610:	59                   	pop    %cx
    4611:	4c                   	dec    %sp
    4612:	45                   	inc    %bp
    4613:	58                   	pop    %ax
    4614:	20 43 6f             	and    %al,0x6f(%bp,%di)
    4617:	72 70                	jb     0x4689
    4619:	6f                   	outsw  %ds:(%si),(%dx)
    461a:	72 61                	jb     0x467d
    461c:	74 69                	je     0x4687
    461e:	6f                   	outsw  %ds:(%si),(%dx)
    461f:	6e                   	outsb  %ds:(%si),(%dx)
    4620:	00 53 49             	add    %dl,0x49(%bp,%di)
    4623:	45                   	inc    %bp
    4624:	4d                   	dec    %bp
    4625:	45                   	inc    %bp
    4626:	4e                   	dec    %si
    4627:	53                   	push   %bx
    4628:	20 41 47             	and    %al,0x47(%bx,%di)
    462b:	0d 0a 4d             	or     $0x4d0a,%ax
    462e:	79 6c                	jns    0x469c
    4630:	65 78 20             	gs js  0x4653
    4633:	43                   	inc    %bx
    4634:	6f                   	outsw  %ds:(%si),(%dx)
    4635:	72 70                	jb     0x46a7
    4637:	6f                   	outsw  %ds:(%si),(%dx)
    4638:	72 61                	jb     0x469b
    463a:	74 69                	je     0x46a5
    463c:	6f                   	outsw  %ds:(%si),(%dx)
    463d:	6e                   	outsb  %ds:(%si),(%dx)
    463e:	0d 0a 00             	or     $0xa,%ax
    4641:	00 00                	add    %al,(%bx,%si)
    4643:	00 00                	add    %al,(%bx,%si)
    4645:	4d                   	dec    %bp
    4646:	79 6c                	jns    0x46b4
    4648:	65 78 00             	gs js  0x464b
    464b:	0d 0a 44             	or     $0x440a,%ax
    464e:	41                   	inc    %cx
    464f:	43                   	inc    %bx
    4650:	39 36 30 20          	cmp    %si,0x2030
    4654:	42                   	inc    %dx
    4655:	49                   	dec    %cx
    4656:	4f                   	dec    %di
    4657:	53                   	push   %bx
    4658:	20 56 65             	and    %dl,0x65(%bp)
    465b:	72 73                	jb     0x46d0
    465d:	69 6f 6e 20 00       	imul   $0x20,0x6e(%bx),%bp
    4662:	0d 0a 0a             	or     $0xa0a,%ax
    4665:	41                   	inc    %cx
    4666:	64 64 69 74 69 6f 6e 	fs imul $0x6e6f,%fs:0x69(%si),%si
    466d:	61                   	popa   
    466e:	6c                   	insb   (%dx),%es:(%di)
    466f:	20 44 41             	and    %al,0x41(%si)
    4672:	43                   	inc    %bx
    4673:	39 36 30 28          	cmp    %si,0x2830
    4677:	00 29                	add    %ch,(%bx,%di)
    4679:	20 66 6f             	and    %ah,0x6f(%bp)
    467c:	75 6e                	jne    0x46ec
    467e:	64 0d 0a 00          	fs or  $0xa,%ax
    4682:	0d 0a 07             	or     $0x70a,%ax
    4685:	44                   	inc    %sp
    4686:	41                   	inc    %cx
    4687:	43                   	inc    %bx
    4688:	39 36 30 20          	cmp    %si,0x2030
    468c:	6e                   	outsb  %ds:(%si),(%dx)
    468d:	6f                   	outsw  %ds:(%si),(%dx)
    468e:	74 20                	je     0x46b0
    4690:	72 65                	jb     0x46f7
    4692:	73 70                	jae    0x4704
    4694:	6f                   	outsw  %ds:(%si),(%dx)
    4695:	6e                   	outsb  %ds:(%si),(%dx)
    4696:	64 69 6e 67 2d 6e    	imul   $0x6e2d,%fs:0x67(%bp),%bp
    469c:	6f                   	outsw  %ds:(%si),(%dx)
    469d:	20 64 72             	and    %ah,0x72(%si)
    46a0:	69 76 65 73 20       	imul   $0x2073,0x65(%bp),%si
    46a5:	69 6e 73 74 61       	imul   $0x6174,0x73(%bp),%bp
    46aa:	6c                   	insb   (%dx),%es:(%di)
    46ab:	6c                   	insb   (%dx),%es:(%di)
    46ac:	65 64 21 00          	gs and %ax,%fs:(%bx,%si)
    46b0:	0d 0a 07             	or     $0x70a,%ax
    46b3:	4e                   	dec    %si
    46b4:	6f                   	outsw  %ds:(%si),(%dx)
    46b5:	20 66 72             	and    %ah,0x72(%bp)
    46b8:	65 65 20 52 41       	gs and %dl,%gs:0x41(%bp,%si)
    46bd:	4d                   	dec    %bp
    46be:	20 66 6f             	and    %ah,0x6f(%bp)
    46c1:	75 6e                	jne    0x4731
    46c3:	64 20 66 6f          	and    %ah,%fs:0x6f(%bp)
    46c7:	72 20                	jb     0x46e9
    46c9:	44                   	inc    %sp
    46ca:	41                   	inc    %cx
    46cb:	43                   	inc    %bx
    46cc:	39 36 30 20          	cmp    %si,0x2030
    46d0:	6f                   	outsw  %ds:(%si),(%dx)
    46d1:	70 65                	jo     0x4738
    46d3:	72 61                	jb     0x4736
    46d5:	74 69                	je     0x4740
    46d7:	6f                   	outsw  %ds:(%si),(%dx)
    46d8:	6e                   	outsb  %ds:(%si),(%dx)
    46d9:	2d 20 75             	sub    $0x7520,%ax
    46dc:	73 69                	jae    0x4747
    46de:	6e                   	outsb  %ds:(%si),(%dx)
    46df:	67 20 37             	and    %dh,(%edi)
    46e2:	30 30                	xor    %dh,(%bx,%si)
    46e4:	30 3a                	xor    %bh,(%bp,%si)
    46e6:	30 30                	xor    %dh,(%bx,%si)
    46e8:	30 30                	xor    %dh,(%bx,%si)
    46ea:	00 4e 6f             	add    %cl,0x6f(%bp)
    46ed:	20 73 79             	and    %dh,0x79(%bp,%di)
    46f0:	73 74                	jae    0x4766
    46f2:	65 6d                	gs insw (%dx),%es:(%di)
    46f4:	20 64 72             	and    %ah,0x72(%si)
    46f7:	69 76 65 73 20       	imul   $0x2073,0x65(%bp),%si
    46fc:	69 6e 73 74 61       	imul   $0x6174,0x73(%bp),%bp
    4701:	6c                   	insb   (%dx),%es:(%di)
    4702:	6c                   	insb   (%dx),%es:(%di)
    4703:	65 64 07             	gs fs pop %es
    4706:	00 0d                	add    %cl,(%di)
    4708:	0a 07                	or     (%bx),%al
    470a:	53                   	push   %bx
    470b:	43                   	inc    %bx
    470c:	53                   	push   %bx
    470d:	49                   	dec    %cx
    470e:	20 64 65             	and    %ah,0x65(%si)
    4711:	76 69                	jbe    0x477c
    4713:	63 65 20             	arpl   %sp,0x20(%di)
    4716:	61                   	popa   
    4717:	74 20                	je     0x4739
    4719:	43                   	inc    %bx
    471a:	68 61 6e             	push   $0x6e61
    471d:	6e                   	outsb  %ds:(%si),(%dx)
    471e:	65 6c                	gs insb (%dx),%es:(%di)
    4720:	3d 00 20             	cmp    $0x2000,%ax
    4723:	6e                   	outsb  %ds:(%si),(%dx)
    4724:	6f                   	outsw  %ds:(%si),(%dx)
    4725:	74 20                	je     0x4747
    4727:	72 65                	jb     0x478e
    4729:	73 70                	jae    0x479b
    472b:	6f                   	outsw  %ds:(%si),(%dx)
    472c:	6e                   	outsb  %ds:(%si),(%dx)
    472d:	64 69 6e 67 21 00    	imul   $0x21,%fs:0x67(%bp),%bp
    4733:	0d 0a 07             	or     $0x70a,%ax
    4736:	49                   	dec    %cx
    4737:	6e                   	outsb  %ds:(%si),(%dx)
    4738:	73 74                	jae    0x47ae
    473a:	61                   	popa   
    473b:	6c                   	insb   (%dx),%es:(%di)
    473c:	6c                   	insb   (%dx),%es:(%di)
    473d:	61                   	popa   
    473e:	74 69                	je     0x47a9
    4740:	6f                   	outsw  %ds:(%si),(%dx)
    4741:	6e                   	outsb  %ds:(%si),(%dx)
    4742:	20 61 62             	and    %ah,0x62(%bx,%di)
    4745:	6f                   	outsw  %ds:(%si),(%dx)
    4746:	72 74                	jb     0x47bc
    4748:	65 64 00 0d          	gs add %cl,%fs:(%di)
    474c:	0a 07                	or     (%bx),%al
    474e:	44                   	inc    %sp
    474f:	41                   	inc    %cx
    4750:	43                   	inc    %bx
    4751:	39 36 30 20          	cmp    %si,0x2030
    4755:	66 61                	popal  
    4757:	74 61                	je     0x47ba
    4759:	6c                   	insb   (%dx),%es:(%di)
    475a:	20 65 72             	and    %ah,0x72(%di)
    475d:	72 6f                	jb     0x47ce
    475f:	72 20                	jb     0x4781
    4761:	2d 20 6d             	sub    $0x6d20,%ax
    4764:	65 6d                	gs insw (%dx),%es:(%di)
    4766:	6f                   	outsw  %ds:(%si),(%dx)
    4767:	72 79                	jb     0x47e2
    4769:	20 74 65             	and    %dh,0x65(%si)
    476c:	73 74                	jae    0x47e2
    476e:	20 66 61             	and    %ah,0x61(%bp)
    4771:	69 6c 65 64 21       	imul   $0x2164,0x65(%si),%bp
    4776:	00 0d                	add    %cl,(%di)
    4778:	0a 07                	or     (%bx),%al
    477a:	44                   	inc    %sp
    477b:	41                   	inc    %cx
    477c:	43                   	inc    %bx
    477d:	39 36 30 20          	cmp    %si,0x2030
    4781:	66 61                	popal  
    4783:	74 61                	je     0x47e6
    4785:	6c                   	insb   (%dx),%es:(%di)
    4786:	20 65 72             	and    %ah,0x72(%di)
    4789:	72 6f                	jb     0x47fa
    478b:	72 20                	jb     0x47ad
    478d:	2d 20 63             	sub    $0x6320,%ax
    4790:	6f                   	outsw  %ds:(%si),(%dx)
    4791:	6d                   	insw   (%dx),%es:(%di)
    4792:	6d                   	insw   (%dx),%es:(%di)
    4793:	61                   	popa   
    4794:	6e                   	outsb  %ds:(%si),(%dx)
    4795:	64 20 69 6e          	and    %ch,%fs:0x6e(%bx,%di)
    4799:	74 65                	je     0x4800
    479b:	72 66                	jb     0x4803
    479d:	61                   	popa   
    479e:	63 65 20             	arpl   %sp,0x20(%di)
    47a1:	74 65                	je     0x4808
    47a3:	73 74                	jae    0x4819
    47a5:	20 66 61             	and    %ah,0x61(%bp)
    47a8:	69 6c 65 64 21       	imul   $0x2164,0x65(%si),%bp
    47ad:	00 0d                	add    %cl,(%di)
    47af:	0a 07                	or     (%bx),%al
    47b1:	44                   	inc    %sp
    47b2:	41                   	inc    %cx
    47b3:	43                   	inc    %bx
    47b4:	39 36 30 20          	cmp    %si,0x2030
    47b8:	68 61 72             	push   $0x7261
    47bb:	64 77 61             	fs ja  0x481f
    47be:	72 65                	jb     0x4825
    47c0:	20 65 72             	and    %ah,0x72(%di)
    47c3:	72 6f                	jb     0x4834
    47c5:	72 20                	jb     0x47e7
    47c7:	2d 20 52             	sub    $0x5220,%ax
    47ca:	75 6e                	jne    0x483a
    47cc:	20 44 69             	and    %al,0x69(%si)
    47cf:	61                   	popa   
    47d0:	67 6e                	outsb  %ds:(%esi),(%dx)
    47d2:	6f                   	outsw  %ds:(%si),(%dx)
    47d3:	73 74                	jae    0x4849
    47d5:	69 63 73 20 74       	imul   $0x7420,0x73(%bp,%di),%sp
    47da:	6f                   	outsw  %ds:(%si),(%dx)
    47db:	20 70 69             	and    %dh,0x69(%bx,%si)
    47de:	6e                   	outsb  %ds:(%si),(%dx)
    47df:	70 6f                	jo     0x4850
    47e1:	69 6e 74 20 65       	imul   $0x6520,0x74(%bp),%bp
    47e6:	72 72                	jb     0x485a
    47e8:	6f                   	outsw  %ds:(%si),(%dx)
    47e9:	72 00                	jb     0x47eb
    47eb:	0d 0a 07             	or     $0x70a,%ax
    47ee:	44                   	inc    %sp
    47ef:	41                   	inc    %cx
    47f0:	43                   	inc    %bx
    47f1:	39 36 30 20          	cmp    %si,0x2030
    47f5:	66 69 72 6d 77 61 72 	imul   $0x65726177,0x6d(%bp,%si),%esi
    47fc:	65 
    47fd:	20 63 68             	and    %ah,0x68(%bp,%di)
    4800:	65 63 6b 73          	arpl   %bp,%gs:0x73(%bp,%di)
    4804:	75 6d                	jne    0x4873
    4806:	20 65 72             	and    %ah,0x72(%di)
    4809:	72 6f                	jb     0x487a
    480b:	72 20                	jb     0x482d
    480d:	2d 20 72             	sub    $0x7220,%ax
    4810:	65 6c                	gs insb (%dx),%es:(%di)
    4812:	6f                   	outsw  %ds:(%si),(%dx)
    4813:	61                   	popa   
    4814:	64 20 66 69          	and    %ah,%fs:0x69(%bp)
    4818:	72 6d                	jb     0x4887
    481a:	77 61                	ja     0x487d
    481c:	72 65                	jb     0x4883
    481e:	00 0d                	add    %cl,(%di)
    4820:	0a 07                	or     (%bx),%al
    4822:	44                   	inc    %sp
    4823:	41                   	inc    %cx
    4824:	43                   	inc    %bx
    4825:	39 36 30 20          	cmp    %si,0x2030
    4829:	63 6f 6e             	arpl   %bp,0x6e(%bx)
    482c:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    4833:	69 
    4834:	6f                   	outsw  %ds:(%si),(%dx)
    4835:	6e                   	outsb  %ds:(%si),(%dx)
    4836:	20 63 68             	and    %ah,0x68(%bp,%di)
    4839:	65 63 6b 73          	arpl   %bp,%gs:0x73(%bp,%di)
    483d:	75 6d                	jne    0x48ac
    483f:	20 65 72             	and    %ah,0x72(%di)
    4842:	72 6f                	jb     0x48b3
    4844:	72 20                	jb     0x4866
    4846:	2d 20 52             	sub    $0x5220,%ax
    4849:	75 6e                	jne    0x48b9
    484b:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    484e:	6e                   	outsb  %ds:(%si),(%dx)
    484f:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    4856:	69 
    4857:	6f                   	outsw  %ds:(%si),(%dx)
    4858:	6e                   	outsb  %ds:(%si),(%dx)
    4859:	20 75 74             	and    %dh,0x74(%di)
    485c:	69 6c 69 74 79       	imul   $0x7974,0x69(%si),%bp
    4861:	21 00                	and    %ax,(%bx,%si)
    4863:	0d 0a 07             	or     $0x70a,%ax
    4866:	44                   	inc    %sp
    4867:	41                   	inc    %cx
    4868:	43                   	inc    %bx
    4869:	39 36 30 20          	cmp    %si,0x2030
    486d:	4d                   	dec    %bp
    486e:	69 73 6d 61 74       	imul   $0x7461,0x6d(%bp,%di),%si
    4873:	63 68 20             	arpl   %bp,0x20(%bx,%si)
    4876:	62 65 74             	bound  %sp,0x74(%di)
    4879:	77 65                	ja     0x48e0
    487b:	65 6e                	outsb  %gs:(%si),(%dx)
    487d:	20 4e 56             	and    %cl,0x56(%bp)
    4880:	52                   	push   %dx
    4881:	41                   	inc    %cx
    4882:	4d                   	dec    %bp
    4883:	20 26 20 46          	and    %ah,0x4620
    4887:	6c                   	insb   (%dx),%es:(%di)
    4888:	61                   	popa   
    4889:	73 68                	jae    0x48f3
    488b:	20 45 45             	and    %al,0x45(%di)
    488e:	50                   	push   %ax
    488f:	52                   	push   %dx
    4890:	4f                   	dec    %di
    4891:	4d                   	dec    %bp
    4892:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    4895:	6e                   	outsb  %ds:(%si),(%dx)
    4896:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    489d:	69 
    489e:	6f                   	outsw  %ds:(%si),(%dx)
    489f:	6e                   	outsb  %ds:(%si),(%dx)
    48a0:	73 20                	jae    0x48c2
    48a2:	21 00                	and    %ax,(%bx,%si)
    48a4:	0d 0a 07             	or     $0x70a,%ax
    48a7:	44                   	inc    %sp
    48a8:	41                   	inc    %cx
    48a9:	43                   	inc    %bx
    48aa:	39 36 30 20          	cmp    %si,0x2030
    48ae:	46                   	inc    %si
    48af:	61                   	popa   
    48b0:	74 61                	je     0x4913
    48b2:	6c                   	insb   (%dx),%es:(%di)
    48b3:	20 65 72             	and    %ah,0x72(%di)
    48b6:	72 6f                	jb     0x4927
    48b8:	72 20                	jb     0x48da
    48ba:	2d 20 6d             	sub    $0x6d20,%ax
    48bd:	65 6d                	gs insw (%dx),%es:(%di)
    48bf:	6f                   	outsw  %ds:(%si),(%dx)
    48c0:	72 79                	jb     0x493b
    48c2:	20 70 61             	and    %dh,0x61(%bx,%si)
    48c5:	72 69                	jb     0x4930
    48c7:	74 79                	je     0x4942
    48c9:	20 66 61             	and    %ah,0x61(%bp)
    48cc:	69 6c 75 72 65       	imul   $0x6572,0x75(%si),%bp
    48d1:	21 00                	and    %ax,(%bx,%si)
    48d3:	0d 0a 07             	or     $0x70a,%ax
    48d6:	44                   	inc    %sp
    48d7:	41                   	inc    %cx
    48d8:	43                   	inc    %bx
    48d9:	39 36 30 20          	cmp    %si,0x2030
    48dd:	63 61 6e             	arpl   %sp,0x6e(%bx,%di)
    48e0:	6e                   	outsb  %ds:(%si),(%dx)
    48e1:	6f                   	outsw  %ds:(%si),(%dx)
    48e2:	74 20                	je     0x4904
    48e4:	72 65                	jb     0x494b
    48e6:	63 6f 76             	arpl   %bp,0x76(%bx)
    48e9:	65 72 20             	gs jb  0x490c
    48ec:	66 72 6f             	data32 jb 0x495e
    48ef:	6d                   	insw   (%dx),%es:(%di)
    48f0:	20 6d 69             	and    %ch,0x69(%di)
    48f3:	72 72                	jb     0x4967
    48f5:	6f                   	outsw  %ds:(%si),(%dx)
    48f6:	72 20                	jb     0x4918
    48f8:	72 61                	jb     0x495b
    48fa:	63 65 21             	arpl   %sp,0x21(%di)
    48fd:	0d 0a 53             	or     $0x530a,%ax
    4900:	6f                   	outsw  %ds:(%si),(%dx)
    4901:	6d                   	insw   (%dx),%es:(%di)
    4902:	65 20 73 79          	and    %dh,%gs:0x79(%bp,%di)
    4906:	73 74                	jae    0x497c
    4908:	65 6d                	gs insw (%dx),%es:(%di)
    490a:	20 64 72             	and    %ah,0x72(%si)
    490d:	69 76 65 73 20       	imul   $0x2073,0x65(%bp),%si
    4912:	61                   	popa   
    4913:	72 65                	jb     0x497a
    4915:	20 69 6e             	and    %ch,0x6e(%bx,%di)
    4918:	63 6f 6e             	arpl   %bp,0x6e(%bx)
    491b:	73 69                	jae    0x4986
    491d:	73 74                	jae    0x4993
    491f:	65 6e                	outsb  %gs:(%si),(%dx)
    4921:	74 21                	je     0x4944
    4923:	00 0d                	add    %cl,(%di)
    4925:	0a 07                	or     (%bx),%al
    4927:	4d                   	dec    %bp
    4928:	69 72 72 6f 72       	imul   $0x726f,0x72(%bp,%si),%si
    492d:	20 72 61             	and    %dh,0x61(%bp,%si)
    4930:	63 65 20             	arpl   %sp,0x20(%di)
    4933:	6f                   	outsw  %ds:(%si),(%dx)
    4934:	6e                   	outsb  %ds:(%si),(%dx)
    4935:	20 63 72             	and    %ah,0x72(%bp,%di)
    4938:	69 74 69 63 61       	imul   $0x6163,0x69(%si),%si
    493d:	6c                   	insb   (%dx),%es:(%di)
    493e:	20 73 79             	and    %dh,0x79(%bp,%di)
    4941:	73 74                	jae    0x49b7
    4943:	65 6d                	gs insw (%dx),%es:(%di)
    4945:	20 64 72             	and    %ah,0x72(%si)
    4948:	69 76 65 20 21       	imul   $0x2120,0x65(%bp),%si
    494d:	0d 0a 53             	or     $0x530a,%ax
    4950:	6f                   	outsw  %ds:(%si),(%dx)
    4951:	6d                   	insw   (%dx),%es:(%di)
    4952:	65 20 73 79          	and    %dh,%gs:0x79(%bp,%di)
    4956:	73 74                	jae    0x49cc
    4958:	65 6d                	gs insw (%dx),%es:(%di)
    495a:	20 64 72             	and    %ah,0x72(%si)
    495d:	69 76 65 73 20       	imul   $0x2073,0x65(%bp),%si
    4962:	61                   	popa   
    4963:	72 65                	jb     0x49ca
    4965:	20 69 6e             	and    %ch,0x6e(%bx,%di)
    4968:	63 6f 6e             	arpl   %bp,0x6e(%bx)
    496b:	73 69                	jae    0x49d6
    496d:	73 74                	jae    0x49e3
    496f:	65 6e                	outsb  %gs:(%si),(%dx)
    4971:	74 20                	je     0x4993
    4973:	21 00                	and    %ax,(%bx,%si)
    4975:	0d 0a 07             	or     $0x70a,%ax
    4978:	52                   	push   %dx
    4979:	65 63 6f 76          	arpl   %bp,%gs:0x76(%bx)
    497d:	65 72 79             	gs jb  0x49f9
    4980:	20 66 72             	and    %ah,0x72(%bp)
    4983:	6f                   	outsw  %ds:(%si),(%dx)
    4984:	6d                   	insw   (%dx),%es:(%di)
    4985:	20 6d 69             	and    %ch,0x69(%di)
    4988:	72 72                	jb     0x49fc
    498a:	6f                   	outsw  %ds:(%si),(%dx)
    498b:	72 20                	jb     0x49ad
    498d:	72 61                	jb     0x49f0
    498f:	63 65 20             	arpl   %sp,0x20(%di)
    4992:	69 6e 20 70 72       	imul   $0x7270,0x20(%bp),%bp
    4997:	6f                   	outsw  %ds:(%si),(%dx)
    4998:	67 72 65             	addr32 jb 0x4a00
    499b:	73 73                	jae    0x4a10
    499d:	00 0d                	add    %cl,(%di)
    499f:	0a 07                	or     (%bx),%al
    49a1:	44                   	inc    %sp
    49a2:	41                   	inc    %cx
    49a3:	43                   	inc    %bx
    49a4:	39 36 30 20          	cmp    %si,0x2030
    49a8:	57                   	push   %di
    49a9:	6f                   	outsw  %ds:(%si),(%dx)
    49aa:	72 6b                	jb     0x4a17
    49ac:	69 6e 67 20 69       	imul   $0x6920,0x67(%bp),%bp
    49b1:	6e                   	outsb  %ds:(%si),(%dx)
    49b2:	20 63 6c             	and    %ah,0x6c(%bp,%di)
    49b5:	75 73                	jne    0x4a2a
    49b7:	74 65                	je     0x4a1e
    49b9:	72 65                	jb     0x4a20
    49bb:	64 20 6d 6f          	and    %ch,%fs:0x6f(%di)
    49bf:	64 65 00 0d          	fs add %cl,%gs:(%di)
    49c3:	0a 07                	or     (%bx),%al
    49c5:	44                   	inc    %sp
    49c6:	65 76 69             	gs jbe 0x4a32
    49c9:	63 65 20             	arpl   %sp,0x20(%di)
    49cc:	69 64 65 6e 74       	imul   $0x746e,0x65(%si),%sp
    49d1:	69 66 69 65 64       	imul   $0x6465,0x69(%bp),%sp
    49d6:	20 66 6f             	and    %ah,0x6f(%bp)
    49d9:	72 20                	jb     0x49fb
    49db:	43                   	inc    %bx
    49dc:	68 61 6e             	push   $0x6e61
    49df:	6e                   	outsb  %ds:(%si),(%dx)
    49e0:	65 6c                	gs insb (%dx),%es:(%di)
    49e2:	3d 00 0d             	cmp    $0xd00,%ax
    49e5:	0a 07                	or     (%bx),%al
    49e7:	55                   	push   %bp
    49e8:	6e                   	outsb  %ds:(%si),(%dx)
    49e9:	69 64 65 6e 74       	imul   $0x746e,0x65(%si),%sp
    49ee:	69 66 69 65 64       	imul   $0x6465,0x69(%bp),%sp
    49f3:	20 64 65             	and    %ah,0x65(%si)
    49f6:	76 69                	jbe    0x4a61
    49f8:	63 65 00             	arpl   %sp,0x0(%di)
    49fb:	20 66 6f             	and    %ah,0x6f(%bp)
    49fe:	75 6e                	jne    0x4a6e
    4a00:	64 20 61 74          	and    %ah,%fs:0x74(%bx,%di)
    4a04:	20 43 68             	and    %al,0x68(%bp,%di)
    4a07:	61                   	popa   
    4a08:	6e                   	outsb  %ds:(%si),(%dx)
    4a09:	6e                   	outsb  %ds:(%si),(%dx)
    4a0a:	65 6c                	gs insb (%dx),%es:(%di)
    4a0c:	3d 00 0d             	cmp    $0xd00,%ax
    4a0f:	53                   	push   %bx
    4a10:	70 69                	jo     0x4a7b
    4a12:	6e                   	outsb  %ds:(%si),(%dx)
    4a13:	6e                   	outsb  %ds:(%si),(%dx)
    4a14:	69 6e 67 20 75       	imul   $0x7520,0x67(%bp),%bp
    4a19:	70 20                	jo     0x4a3b
    4a1b:	64 72 69             	fs jb  0x4a87
    4a1e:	76 65                	jbe    0x4a85
    4a20:	73 2e                	jae    0x4a50
    4a22:	00 20                	add    %ah,(%bx,%si)
    4a24:	73 79                	jae    0x4a9f
    4a26:	73 74                	jae    0x4a9c
    4a28:	65 6d                	gs insw (%dx),%es:(%di)
    4a2a:	20 64 72             	and    %ah,0x72(%si)
    4a2d:	69 76 65 20 20       	imul   $0x2020,0x65(%bp),%si
    4a32:	69 6e 73 74 61       	imul   $0x6174,0x73(%bp),%bp
    4a37:	6c                   	insb   (%dx),%es:(%di)
    4a38:	6c                   	insb   (%dx),%es:(%di)
    4a39:	65 64 00 20          	gs add %ah,%fs:(%bx,%si)
    4a3d:	73 79                	jae    0x4ab8
    4a3f:	73 74                	jae    0x4ab5
    4a41:	65 6d                	gs insw (%dx),%es:(%di)
    4a43:	20 64 72             	and    %ah,0x72(%si)
    4a46:	69 76 65 20 20       	imul   $0x2020,0x65(%bp),%si
    4a4b:	66 6f                	outsl  %ds:(%si),(%dx)
    4a4d:	75 6e                	jne    0x4abd
    4a4f:	64 0d 0a 42          	fs or  $0x420a,%ax
    4a53:	49                   	dec    %cx
    4a54:	4f                   	dec    %di
    4a55:	53                   	push   %bx
    4a56:	20 64 69             	and    %ah,0x69(%si)
    4a59:	73 61                	jae    0x4abc
    4a5b:	62 6c 65             	bound  %bp,0x65(%si)
    4a5e:	64 21 00             	and    %ax,%fs:(%bx,%si)
    4a61:	0d 0a 07             	or     $0x70a,%ax
    4a64:	57                   	push   %di
    4a65:	41                   	inc    %cx
    4a66:	52                   	push   %dx
    4a67:	4e                   	dec    %si
    4a68:	49                   	dec    %cx
    4a69:	4e                   	dec    %si
    4a6a:	47                   	inc    %di
    4a6b:	3a 20                	cmp    (%bx,%si),%ah
    4a6d:	54                   	push   %sp
    4a6e:	68 65 20             	push   $0x2065
    4a71:	46                   	inc    %si
    4a72:	69 72 6d 77 61       	imul   $0x6177,0x6d(%bp,%si),%si
    4a77:	72 65                	jb     0x4ade
    4a79:	20 46 6c             	and    %al,0x6c(%bp)
    4a7c:	61                   	popa   
    4a7d:	73 68                	jae    0x4ae7
    4a7f:	20 45 45             	and    %al,0x45(%di)
    4a82:	50                   	push   %ax
    4a83:	52                   	push   %dx
    4a84:	4f                   	dec    %di
    4a85:	4d                   	dec    %bp
    4a86:	20 69 73             	and    %ch,0x73(%bx,%di)
    4a89:	20 72 65             	and    %dh,0x65(%bp,%si)
    4a8c:	61                   	popa   
    4a8d:	63 68 69             	arpl   %bp,0x69(%bx,%si)
    4a90:	6e                   	outsb  %ds:(%si),(%dx)
    4a91:	67 20 74 68 65       	and    %dh,0x65(%eax,%ebp,2)
    4a96:	20 65 6e             	and    %ah,0x6e(%di)
    4a99:	64 20 6f 66          	and    %ch,%fs:0x66(%bx)
    4a9d:	20 69 74             	and    %ch,0x74(%bx,%di)
    4aa0:	73 20                	jae    0x4ac2
    4aa2:	6c                   	insb   (%dx),%es:(%di)
    4aa3:	69 66 65 0d 0a       	imul   $0xa0d,0x65(%bp),%sp
    4aa8:	49                   	dec    %cx
    4aa9:	74 20                	je     0x4acb
    4aab:	73 68                	jae    0x4b15
    4aad:	6f                   	outsw  %ds:(%si),(%dx)
    4aae:	75 6c                	jne    0x4b1c
    4ab0:	64 20 62 65          	and    %ah,%fs:0x65(%bp,%si)
    4ab4:	20 72 65             	and    %dh,0x65(%bp,%si)
    4ab7:	70 6c                	jo     0x4b25
    4ab9:	61                   	popa   
    4aba:	63 65 64             	arpl   %sp,0x64(%di)
    4abd:	20 41 53             	and    %al,0x53(%bx,%di)
    4ac0:	41                   	inc    %cx
    4ac1:	50                   	push   %ax
    4ac2:	00 0d                	add    %cl,(%di)
    4ac4:	0a 07                	or     (%bx),%al
    4ac6:	57                   	push   %di
    4ac7:	41                   	inc    %cx
    4ac8:	52                   	push   %dx
    4ac9:	4e                   	dec    %si
    4aca:	49                   	dec    %cx
    4acb:	4e                   	dec    %si
    4acc:	47                   	inc    %di
    4acd:	3a 20                	cmp    (%bx,%si),%ah
    4acf:	00 20                	add    %ah,(%bx,%si)
    4ad1:	73 79                	jae    0x4b4c
    4ad3:	73 74                	jae    0x4b49
    4ad5:	65 6d                	gs insw (%dx),%es:(%di)
    4ad7:	20 64 72             	and    %ah,0x72(%si)
    4ada:	69 76 65 20 20       	imul   $0x2020,0x65(%bp),%si
    4adf:	63 72 69             	arpl   %si,0x69(%bp,%si)
    4ae2:	74 69                	je     0x4b4d
    4ae4:	63 61 6c             	arpl   %sp,0x6c(%bx,%di)
    4ae7:	00 20                	add    %ah,(%bx,%si)
    4ae9:	73 79                	jae    0x4b64
    4aeb:	73 74                	jae    0x4b61
    4aed:	65 6d                	gs insw (%dx),%es:(%di)
    4aef:	20 64 72             	and    %ah,0x72(%si)
    4af2:	69 76 65 20 20       	imul   $0x2020,0x65(%bp),%si
    4af7:	6f                   	outsw  %ds:(%si),(%dx)
    4af8:	66 66 6c             	data32 data32 insb (%dx),%es:(%di)
    4afb:	69 6e 65 00 0d       	imul   $0xd00,0x65(%bp),%bp
    4b00:	0a 44 41             	or     0x41(%si),%al
    4b03:	43                   	inc    %bx
    4b04:	39 36 30 20          	cmp    %si,0x2030
    4b08:	4d                   	dec    %bp
    4b09:	65 6d                	gs insw (%dx),%es:(%di)
    4b0b:	6f                   	outsw  %ds:(%si),(%dx)
    4b0c:	72 79                	jb     0x4b87
    4b0e:	20 3d                	and    %bh,(%di)
    4b10:	20 00                	and    %al,(%bx,%si)
    4b12:	20 4d 42             	and    %cl,0x42(%di)
    4b15:	00 20                	add    %ah,(%bx,%si)
    4b17:	28 44 52             	sub    %al,0x52(%si)
    4b1a:	41                   	inc    %cx
    4b1b:	4d                   	dec    %bp
    4b1c:	29 00                	sub    %ax,(%bx,%si)
    4b1e:	20 28                	and    %ch,(%bx,%si)
    4b20:	45                   	inc    %bp
    4b21:	44                   	inc    %sp
    4b22:	52                   	push   %dx
    4b23:	41                   	inc    %cx
    4b24:	4d                   	dec    %bp
    4b25:	29 00                	sub    %ax,(%bx,%si)
    4b27:	20 28                	and    %ch,(%bx,%si)
    4b29:	45                   	inc    %bp
    4b2a:	44                   	inc    %sp
    4b2b:	4f                   	dec    %di
    4b2c:	20 52 41             	and    %dl,0x41(%bp,%si)
    4b2f:	4d                   	dec    %bp
    4b30:	29 00                	sub    %ax,(%bx,%si)
    4b32:	20 28                	and    %ch,(%bx,%si)
    4b34:	45                   	inc    %bp
    4b35:	44                   	inc    %sp
    4b36:	4f                   	dec    %di
    4b37:	00 20                	add    %ah,(%bx,%si)
    4b39:	28 53 44             	sub    %dl,0x44(%bp,%di)
    4b3c:	52                   	push   %dx
    4b3d:	41                   	inc    %cx
    4b3e:	4d                   	dec    %bp
    4b3f:	00 2f                	add    %ch,(%bx)
    4b41:	50                   	push   %ax
    4b42:	61                   	popa   
    4b43:	72 69                	jb     0x4bae
    4b45:	74 79                	je     0x4bc0
    4b47:	29 00                	sub    %ax,(%bx,%si)
    4b49:	29 20                	sub    %sp,(%bx,%si)
    4b4b:	2a 2a                	sub    (%bp,%si),%ch
    4b4d:	2a 4e 6f             	sub    0x6f(%bp),%cl
    4b50:	20 65 72             	and    %ah,0x72(%di)
    4b53:	72 6f                	jb     0x4bc4
    4b55:	72 20                	jb     0x4b77
    4b57:	63 6f 72             	arpl   %bp,0x72(%bx)
    4b5a:	72 65                	jb     0x4bc1
    4b5c:	63 74 69             	arpl   %si,0x69(%si)
    4b5f:	6f                   	outsw  %ds:(%si),(%dx)
    4b60:	6e                   	outsb  %ds:(%si),(%dx)
    4b61:	2a 2a                	sub    (%bp,%si),%ch
    4b63:	2a 00                	sub    (%bx,%si),%al
    4b65:	2f                   	das    
    4b66:	45                   	inc    %bp
    4b67:	43                   	inc    %bx
    4b68:	43                   	inc    %bx
    4b69:	29 00                	sub    %ax,(%bx,%si)
    4b6b:	20 28                	and    %ch,(%bx,%si)
    4b6d:	46                   	inc    %si
    4b6e:	50                   	push   %ax
    4b6f:	4d                   	dec    %bp
    4b70:	00 20                	add    %ah,(%bx,%si)
    4b72:	2f                   	das    
    4b73:	4c                   	dec    %sp
    4b74:	6f                   	outsw  %ds:(%si),(%dx)
    4b75:	77 20                	ja     0x4b97
    4b77:	70 6f                	jo     0x4be8
    4b79:	77 65                	ja     0x4be0
    4b7b:	72 00                	jb     0x4b7d
    4b7d:	0d 0a 07             	or     $0x70a,%ax
    4b80:	57                   	push   %di
    4b81:	41                   	inc    %cx
    4b82:	52                   	push   %dx
    4b83:	4e                   	dec    %si
    4b84:	49                   	dec    %cx
    4b85:	4e                   	dec    %si
    4b86:	47                   	inc    %di
    4b87:	3a 20                	cmp    (%bx,%si),%ah
    4b89:	44                   	inc    %sp
    4b8a:	65 61                	gs popa 
    4b8c:	64 20 53 43          	and    %dl,%fs:0x43(%bp,%di)
    4b90:	53                   	push   %bx
    4b91:	49                   	dec    %cx
    4b92:	20 64 65             	and    %ah,0x65(%si)
    4b95:	76 69                	jbe    0x4c00
    4b97:	63 65 20             	arpl   %sp,0x20(%di)
    4b9a:	20 28                	and    %ch,(%bx,%si)
    4b9c:	43                   	inc    %bx
    4b9d:	68 61 6e             	push   $0x6e61
    4ba0:	6e                   	outsb  %ds:(%si),(%dx)
    4ba1:	65 6c                	gs insb (%dx),%es:(%di)
    4ba3:	3a 54 61             	cmp    0x61(%si),%dl
    4ba6:	72 67                	jb     0x4c0f
    4ba8:	65 74 29             	gs je  0x4bd4
    4bab:	20 3a                	and    %bh,(%bp,%si)
    4bad:	20 0d                	and    %cl,(%di)
    4baf:	0a 00                	or     (%bx,%si),%al
    4bb1:	0d 0a 50             	or     $0x500a,%ax
    4bb4:	72 65                	jb     0x4c1b
    4bb6:	73 73                	jae    0x4c2b
    4bb8:	20 61 6e             	and    %ah,0x6e(%bx,%di)
    4bbb:	79 20                	jns    0x4bdd
    4bbd:	6b 65 79 20          	imul   $0x20,0x79(%di),%sp
    4bc1:	74 6f                	je     0x4c32
    4bc3:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    4bc6:	6e                   	outsb  %ds:(%si),(%dx)
    4bc7:	74 69                	je     0x4c32
    4bc9:	6e                   	outsb  %ds:(%si),(%dx)
    4bca:	75 65                	jne    0x4c31
    4bcc:	00 0d                	add    %cl,(%di)
    4bce:	0a 4e 4f             	or     0x4f(%bp),%cl
    4bd1:	20 41 43             	and    %al,0x43(%bx,%di)
    4bd4:	54                   	push   %sp
    4bd5:	49                   	dec    %cx
    4bd6:	56                   	push   %si
    4bd7:	45                   	inc    %bp
    4bd8:	20 50 41             	and    %dl,0x41(%bx,%si)
    4bdb:	52                   	push   %dx
    4bdc:	54                   	push   %sp
    4bdd:	49                   	dec    %cx
    4bde:	54                   	push   %sp
    4bdf:	49                   	dec    %cx
    4be0:	4f                   	dec    %di
    4be1:	4e                   	dec    %si
    4be2:	00 42 49             	add    %al,0x49(%bp,%si)
    4be5:	4f                   	dec    %di
    4be6:	53                   	push   %bx
    4be7:	20 64 69             	and    %ah,0x69(%si)
    4bea:	73 61                	jae    0x4c4d
    4bec:	62 6c 65             	bound  %bp,0x65(%si)
    4bef:	64 00 42 49          	add    %al,%fs:0x49(%bp,%si)
    4bf3:	4f                   	dec    %di
    4bf4:	53                   	push   %bx
    4bf5:	20 65 6e             	and    %ah,0x6e(%di)
    4bf8:	61                   	popa   
    4bf9:	62 6c 65             	bound  %bp,0x65(%si)
    4bfc:	64 00 43 44          	add    %al,%fs:0x44(%bp,%di)
    4c00:	2d 52 4f             	sub    $0x4f52,%ax
    4c03:	4d                   	dec    %bp
    4c04:	20 62 6f             	and    %ah,0x6f(%bp,%si)
    4c07:	6f                   	outsw  %ds:(%si),(%dx)
    4c08:	74 20                	je     0x4c2a
    4c0a:	64 69 73 61 62 6c    	imul   $0x6c62,%fs:0x61(%bp,%di),%si
    4c10:	65 64 00 43 44       	gs add %al,%fs:0x44(%bp,%di)
    4c15:	2d 52 4f             	sub    $0x4f52,%ax
    4c18:	4d                   	dec    %bp
    4c19:	20 62 6f             	and    %ah,0x6f(%bp,%si)
    4c1c:	6f                   	outsw  %ds:(%si),(%dx)
    4c1d:	74 20                	je     0x4c3f
    4c1f:	65 6e                	outsb  %gs:(%si),(%dx)
    4c21:	61                   	popa   
    4c22:	62 6c 65             	bound  %bp,0x65(%si)
    4c25:	64 00 32             	add    %dh,%fs:(%bp,%si)
    4c28:	20 47 42             	and    %al,0x42(%bx)
    4c2b:	20 64 72             	and    %ah,0x72(%si)
    4c2e:	69 76 65 20 67       	imul   $0x6720,0x65(%bp),%si
    4c33:	65 6f                	outsw  %gs:(%si),(%dx)
    4c35:	6d                   	insw   (%dx),%es:(%di)
    4c36:	65 74 72             	gs je  0x4cab
    4c39:	79 00                	jns    0x4c3b
    4c3b:	38 20                	cmp    %ah,(%bx,%si)
    4c3d:	47                   	inc    %di
    4c3e:	42                   	inc    %dx
    4c3f:	20 64 72             	and    %ah,0x72(%si)
    4c42:	69 76 65 20 67       	imul   $0x6720,0x65(%bp),%si
    4c47:	65 6f                	outsw  %gs:(%si),(%dx)
    4c49:	6d                   	insw   (%dx),%es:(%di)
    4c4a:	65 74 72             	gs je  0x4cbf
    4c4d:	79 00                	jns    0x4c4f
    4c4f:	43                   	inc    %bx
    4c50:	6f                   	outsw  %ds:(%si),(%dx)
    4c51:	6e                   	outsb  %ds:(%si),(%dx)
    4c52:	66 69 67 75 72 65 20 	imul   $0x4d206572,0x75(%bx),%esp
    4c59:	4d 
    4c5a:	44                   	inc    %sp
    4c5b:	41                   	inc    %cx
    4c5c:	43                   	inc    %bx
    4c5d:	00 54 68             	add    %dl,0x68(%si)
    4c60:	65 20 73 79          	and    %dh,%gs:0x79(%bp,%di)
    4c64:	73 74                	jae    0x4cda
    4c66:	65 6d                	gs insw (%dx),%es:(%di)
    4c68:	20 77 69             	and    %dh,0x69(%bx)
    4c6b:	6c                   	insb   (%dx),%es:(%di)
    4c6c:	6c                   	insb   (%dx),%es:(%di)
    4c6d:	20 72 65             	and    %dh,0x65(%bp,%si)
    4c70:	73 74                	jae    0x4ce6
    4c72:	61                   	popa   
    4c73:	72 74                	jb     0x4ce9
    4c75:	20 20                	and    %ah,(%bx,%si)
    4c77:	20 00                	and    %al,(%bx,%si)
    4c79:	50                   	push   %ax
    4c7a:	72 65                	jb     0x4ce1
    4c7c:	73 73                	jae    0x4cf1
    4c7e:	20 61 6e             	and    %ah,0x6e(%bx,%di)
    4c81:	79 20                	jns    0x4ca3
    4c83:	6b 65 79 20          	imul   $0x20,0x79(%di),%sp
    4c87:	74 6f                	je     0x4cf8
    4c89:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    4c8c:	6e                   	outsb  %ds:(%si),(%dx)
    4c8d:	74 69                	je     0x4cf8
    4c8f:	6e                   	outsb  %ds:(%si),(%dx)
    4c90:	75 65                	jne    0x4cf7
    4c92:	20 00                	and    %al,(%bx,%si)
    4c94:	20 55 73             	and    %dl,0x73(%di)
    4c97:	65 20 61 72          	and    %ah,%gs:0x72(%bx,%di)
    4c9b:	72 6f                	jb     0x4d0c
    4c9d:	77 20                	ja     0x4cbf
    4c9f:	6b 65 79 73          	imul   $0x73,0x79(%di),%sp
    4ca3:	20 74 6f             	and    %dh,0x6f(%si)
    4ca6:	20 6d 6f             	and    %ch,0x6f(%di)
    4ca9:	76 65                	jbe    0x4d10
    4cab:	20 74 68             	and    %dh,0x68(%si)
    4cae:	72 6f                	jb     0x4d1f
    4cb0:	75 67                	jne    0x4d19
    4cb2:	68 20 6f             	push   $0x6f20
    4cb5:	70 74                	jo     0x4d2b
    4cb7:	69 6f 6e 73 3b       	imul   $0x3b73,0x6e(%bx),%bp
    4cbc:	20 3c                	and    %bh,(%si)
    4cbe:	45                   	inc    %bp
    4cbf:	4e                   	dec    %si
    4cc0:	54                   	push   %sp
    4cc1:	45                   	inc    %bp
    4cc2:	52                   	push   %dx
    4cc3:	3e 20 74 6f          	and    %dh,%ds:0x6f(%si)
    4cc7:	20 73 65             	and    %dh,0x65(%bp,%di)
    4cca:	6c                   	insb   (%dx),%es:(%di)
    4ccb:	65 63 74 3b          	arpl   %si,%gs:0x3b(%si)
    4ccf:	20 3c                	and    %bh,(%si)
    4cd1:	45                   	inc    %bp
    4cd2:	53                   	push   %bx
    4cd3:	43                   	inc    %bx
    4cd4:	3e 20 74 6f          	and    %dh,%ds:0x6f(%si)
    4cd8:	20 71 75             	and    %dh,0x75(%bx,%di)
    4cdb:	69 74 2e 20 20       	imul   $0x2020,0x2e(%si),%si
    4ce0:	20 20                	and    %ah,(%bx,%si)
    4ce2:	20 20                	and    %ah,(%bx,%si)
    4ce4:	00 42 49             	add    %al,0x49(%bp,%si)
    4ce7:	4f                   	dec    %di
    4ce8:	53                   	push   %bx
    4ce9:	20 69 73             	and    %ch,0x73(%bx,%di)
    4cec:	20 64 69             	and    %ah,0x69(%si)
    4cef:	73 61                	jae    0x4d52
    4cf1:	62 6c 65             	bound  %bp,0x65(%si)
    4cf4:	64 2e 2e 21 20       	fs cs and %sp,%cs:(%bx,%si)
    4cf9:	00 42 49             	add    %al,0x49(%bp,%si)
    4cfc:	4f                   	dec    %di
    4cfd:	53                   	push   %bx
    4cfe:	20 4f 70             	and    %cl,0x70(%bx)
    4d01:	74 69                	je     0x4d6c
    4d03:	6f                   	outsw  %ds:(%si),(%dx)
    4d04:	6e                   	outsb  %ds:(%si),(%dx)
    4d05:	73 00                	jae    0x4d07
    4d07:	44                   	inc    %sp
    4d08:	41                   	inc    %cx
    4d09:	43                   	inc    %bx
    4d0a:	39 36 30 20          	cmp    %si,0x2030
    4d0e:	43                   	inc    %bx
    4d0f:	6f                   	outsw  %ds:(%si),(%dx)
    4d10:	6e                   	outsb  %ds:(%si),(%dx)
    4d11:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    4d18:	69 
    4d19:	6f                   	outsw  %ds:(%si),(%dx)
    4d1a:	6e                   	outsb  %ds:(%si),(%dx)
    4d1b:	20 55 74             	and    %dl,0x74(%di)
    4d1e:	69 6c 69 74 79       	imul   $0x7974,0x69(%si),%bp
    4d23:	20 6e 6f             	and    %ch,0x6f(%bp)
    4d26:	74 20                	je     0x4d48
    4d28:	66 6f                	outsl  %ds:(%si),(%dx)
    4d2a:	75 6e                	jne    0x4d9a
    4d2c:	64 00 c4             	fs add %al,%ah
    4d2f:	c4                   	(bad)  
    4d30:	c4                   	(bad)  
    4d31:	c4                   	(bad)  
    4d32:	c4                   	(bad)  
    4d33:	c4                   	(bad)  
    4d34:	c4                   	(bad)  
    4d35:	c4                   	(bad)  
    4d36:	c4                   	(bad)  
    4d37:	c4                   	(bad)  
    4d38:	c4                   	(bad)  
    4d39:	c4                   	(bad)  
    4d3a:	c4                   	(bad)  
    4d3b:	c4                   	(bad)  
    4d3c:	c4                   	(bad)  
    4d3d:	c4                   	(bad)  
    4d3e:	c4                   	(bad)  
    4d3f:	c4                   	(bad)  
    4d40:	c4                   	(bad)  
    4d41:	c4                   	(bad)  
    4d42:	c4                   	(bad)  
    4d43:	c4                   	(bad)  
    4d44:	c4 00                	les    (%bx,%si),%ax
    4d46:	c4                   	(bad)  
    4d47:	c4                   	(bad)  
    4d48:	c4                   	(bad)  
    4d49:	c4                   	(bad)  
    4d4a:	c4                   	(bad)  
    4d4b:	c4                   	(bad)  
    4d4c:	c4                   	(bad)  
    4d4d:	c4                   	(bad)  
    4d4e:	c4                   	(bad)  
    4d4f:	c4                   	(bad)  
    4d50:	c4                   	(bad)  
    4d51:	c4                   	(bad)  
    4d52:	c4                   	(bad)  
    4d53:	c4 20                	les    (%bx,%si),%sp
    4d55:	57                   	push   %di
    4d56:	41                   	inc    %cx
    4d57:	52                   	push   %dx
    4d58:	4e                   	dec    %si
    4d59:	49                   	dec    %cx
    4d5a:	4e                   	dec    %si
    4d5b:	47                   	inc    %di
    4d5c:	20 c4                	and    %al,%ah
    4d5e:	c4                   	(bad)  
    4d5f:	c4                   	(bad)  
    4d60:	c4                   	(bad)  
    4d61:	c4                   	(bad)  
    4d62:	c4                   	(bad)  
    4d63:	c4                   	(bad)  
    4d64:	c4                   	(bad)  
    4d65:	c4                   	(bad)  
    4d66:	c4                   	(bad)  
    4d67:	c4                   	(bad)  
    4d68:	c4                   	(bad)  
    4d69:	c4                   	(bad)  
    4d6a:	c4 00                	les    (%bx,%si),%ax
    4d6c:	20 43 68             	and    %al,0x68(%bp,%di)
    4d6f:	61                   	popa   
    4d70:	6e                   	outsb  %ds:(%si),(%dx)
    4d71:	67 69 6e 67 20 64    	imul   $0x6420,0x67(%esi),%bp
    4d77:	72 69                	jb     0x4de2
    4d79:	76 65                	jbe    0x4de0
    4d7b:	20 67 65             	and    %ah,0x65(%bx)
    4d7e:	6f                   	outsw  %ds:(%si),(%dx)
    4d7f:	6d                   	insw   (%dx),%es:(%di)
    4d80:	65 74 72             	gs je  0x4df5
    4d83:	79 20                	jns    0x4da5
    4d85:	6d                   	insw   (%dx),%es:(%di)
    4d86:	61                   	popa   
    4d87:	79 20                	jns    0x4da9
    4d89:	6c                   	insb   (%dx),%es:(%di)
    4d8a:	65 61                	gs popa 
    4d8c:	64 20 74 6f          	and    %dh,%fs:0x6f(%si)
    4d90:	20 00                	and    %al,(%bx,%si)
    4d92:	20 6e 6f             	and    %ch,0x6f(%bp)
    4d95:	6e                   	outsb  %ds:(%si),(%dx)
    4d96:	2d 62 6f             	sub    $0x6f62,%ax
    4d99:	6f                   	outsw  %ds:(%si),(%dx)
    4d9a:	74 61                	je     0x4dfd
    4d9c:	62 6c 65             	bound  %bp,0x65(%si)
    4d9f:	20 73 79             	and    %dh,0x79(%bp,%di)
    4da2:	73 74                	jae    0x4e18
    4da4:	65 6d                	gs insw (%dx),%es:(%di)
    4da6:	20 64 72             	and    %ah,0x72(%si)
    4da9:	69 76 65 73 20       	imul   $0x2073,0x65(%bp),%si
    4dae:	61                   	popa   
    4daf:	6e                   	outsb  %ds:(%si),(%dx)
    4db0:	64 2f                	fs das 
    4db2:	6f                   	outsw  %ds:(%si),(%dx)
    4db3:	72 20                	jb     0x4dd5
    4db5:	20 20                	and    %ah,(%bx,%si)
    4db7:	00 20                	add    %ah,(%bx,%si)
    4db9:	6c                   	insb   (%dx),%es:(%di)
    4dba:	6f                   	outsw  %ds:(%si),(%dx)
    4dbb:	73 73                	jae    0x4e30
    4dbd:	20 6f 66             	and    %ch,0x66(%bx)
    4dc0:	20 64 61             	and    %ah,0x61(%si)
    4dc3:	74 61                	je     0x4e26
    4dc5:	21 20                	and    %sp,(%bx,%si)
    4dc7:	20 20                	and    %ah,(%bx,%si)
    4dc9:	20 20                	and    %ah,(%bx,%si)
    4dcb:	20 20                	and    %ah,(%bx,%si)
    4dcd:	20 20                	and    %ah,(%bx,%si)
    4dcf:	20 20                	and    %ah,(%bx,%si)
    4dd1:	20 20                	and    %ah,(%bx,%si)
    4dd3:	20 20                	and    %ah,(%bx,%si)
    4dd5:	20 20                	and    %ah,(%bx,%si)
    4dd7:	20 20                	and    %ah,(%bx,%si)
    4dd9:	20 20                	and    %ah,(%bx,%si)
    4ddb:	20 20                	and    %ah,(%bx,%si)
    4ddd:	00 20                	add    %ah,(%bx,%si)
    4ddf:	50                   	push   %ax
    4de0:	72 6f                	jb     0x4e51
    4de2:	63 65 65             	arpl   %sp,0x65(%di)
    4de5:	64 20 61 6e          	and    %ah,%fs:0x6e(%bx,%di)
    4de9:	79 77                	jns    0x4e62
    4deb:	61                   	popa   
    4dec:	79 3f                	jns    0x4e2d
    4dee:	20 28                	and    %ch,(%bx,%si)
    4df0:	59                   	pop    %cx
    4df1:	2f                   	das    
    4df2:	4e                   	dec    %si
    4df3:	29 20                	sub    %sp,(%bx,%si)
    4df5:	20 20                	and    %ah,(%bx,%si)
    4df7:	20 20                	and    %ah,(%bx,%si)
    4df9:	20 20                	and    %ah,(%bx,%si)
    4dfb:	20 20                	and    %ah,(%bx,%si)
    4dfd:	20 20                	and    %ah,(%bx,%si)
    4dff:	20 20                	and    %ah,(%bx,%si)
    4e01:	20 20                	and    %ah,(%bx,%si)
    4e03:	00 cd                	add    %cl,%ch
    4e05:	00 ba 00 c9          	add    %bh,-0x3700(%bp,%si)
    4e09:	00 bb 00 bc          	add    %bh,-0x4400(%bp,%di)
    4e0d:	00 c8                	add    %cl,%al
    4e0f:	00 c7                	add    %al,%bh
    4e11:	00 b6 00 0d          	add    %dh,0xd00(%bp)
    4e15:	0a 07                	or     (%bx),%al
    4e17:	3c 44                	cmp    $0x44,%al
    4e19:	41                   	inc    %cx
    4e1a:	43                   	inc    %bx
    4e1b:	39 36 30 20          	cmp    %si,0x2030
    4e1f:	42                   	inc    %dx
    4e20:	49                   	dec    %cx
    4e21:	4f                   	dec    %di
    4e22:	53                   	push   %bx
    4e23:	20 69 73             	and    %ch,0x73(%bx,%di)
    4e26:	20 64 69             	and    %ah,0x69(%si)
    4e29:	73 61                	jae    0x4e8c
    4e2b:	62 6c 65             	bound  %bp,0x65(%si)
    4e2e:	64 3e 00 0d          	fs add %cl,%ds:(%di)
    4e32:	0a 3c                	or     (%si),%bh
    4e34:	44                   	inc    %sp
    4e35:	41                   	inc    %cx
    4e36:	43                   	inc    %bx
    4e37:	39 36 30 20          	cmp    %si,0x2030
    4e3b:	32 20                	xor    (%bx,%si),%ah
    4e3d:	47                   	inc    %di
    4e3e:	42                   	inc    %dx
    4e3f:	20 44 69             	and    %al,0x69(%si)
    4e42:	73 6b                	jae    0x4eaf
    4e44:	20 42 49             	and    %al,0x49(%bp,%si)
    4e47:	4f                   	dec    %di
    4e48:	53                   	push   %bx
    4e49:	20 69 73             	and    %ch,0x73(%bx,%di)
    4e4c:	20 65 6e             	and    %ah,0x6e(%di)
    4e4f:	61                   	popa   
    4e50:	62 6c 65             	bound  %bp,0x65(%si)
    4e53:	64 3e 00 0d          	fs add %cl,%ds:(%di)
    4e57:	0a 50 72             	or     0x72(%bx,%si),%dl
    4e5a:	65 73 73             	gs jae 0x4ed0
    4e5d:	20 3c                	and    %bh,(%si)
    4e5f:	41                   	inc    %cx
    4e60:	4c                   	dec    %sp
    4e61:	54                   	push   %sp
    4e62:	2d 52 3e             	sub    $0x3e52,%ax
    4e65:	20 66 6f             	and    %ah,0x6f(%bp)
    4e68:	72 20                	jb     0x4e8a
    4e6a:	52                   	push   %dx
    4e6b:	41                   	inc    %cx
    4e6c:	49                   	dec    %cx
    4e6d:	44                   	inc    %sp
    4e6e:	20 43 6f             	and    %al,0x6f(%bp,%di)
    4e71:	6e                   	outsb  %ds:(%si),(%dx)
    4e72:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    4e79:	69 
    4e7a:	6f                   	outsw  %ds:(%si),(%dx)
    4e7b:	6e                   	outsb  %ds:(%si),(%dx)
    4e7c:	20 6f 70             	and    %ch,0x70(%bx)
    4e7f:	74 69                	je     0x4eea
    4e81:	6f                   	outsw  %ds:(%si),(%dx)
    4e82:	6e                   	outsb  %ds:(%si),(%dx)
    4e83:	73 00                	jae    0x4e85
    4e85:	0d 0a 52             	or     $0x520a,%ax
    4e88:	41                   	inc    %cx
    4e89:	49                   	dec    %cx
    4e8a:	44                   	inc    %sp
    4e8b:	20 43 6f             	and    %al,0x6f(%bp,%di)
    4e8e:	6e                   	outsb  %ds:(%si),(%dx)
    4e8f:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    4e96:	69 
    4e97:	6f                   	outsw  %ds:(%si),(%dx)
    4e98:	6e                   	outsb  %ds:(%si),(%dx)
    4e99:	20 77 69             	and    %dh,0x69(%bx)
    4e9c:	6c                   	insb   (%dx),%es:(%di)
    4e9d:	6c                   	insb   (%dx),%es:(%di)
    4e9e:	20 73 74             	and    %dh,0x74(%bp,%di)
    4ea1:	61                   	popa   
    4ea2:	72 74                	jb     0x4f18
    4ea4:	20 61 66             	and    %ah,0x66(%bx,%di)
    4ea7:	74 65                	je     0x4f0e
    4ea9:	72 20                	jb     0x4ecb
    4eab:	73 79                	jae    0x4f26
    4ead:	73 74                	jae    0x4f23
    4eaf:	65 6d                	gs insw (%dx),%es:(%di)
    4eb1:	20 69 6e             	and    %ch,0x6e(%bx,%di)
    4eb4:	69 74 69 61 6c       	imul   $0x6c61,0x69(%si),%si
    4eb9:	69 7a 61 74 69       	imul   $0x6974,0x61(%bp,%si),%di
    4ebe:	6f                   	outsw  %ds:(%si),(%dx)
    4ebf:	6e                   	outsb  %ds:(%si),(%dx)
    4ec0:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    4ec3:	6d                   	insw   (%dx),%es:(%di)
    4ec4:	70 6c                	jo     0x4f32
    4ec6:	65 74 65             	gs je  0x4f2e
    4ec9:	73 00                	jae    0x4ecb
    4ecb:	0d 0a 50             	or     $0x500a,%ax
    4ece:	72 65                	jb     0x4f35
    4ed0:	73 73                	jae    0x4f45
    4ed2:	20 3c                	and    %bh,(%si)
    4ed4:	41                   	inc    %cx
    4ed5:	4c                   	dec    %sp
    4ed6:	54                   	push   %sp
    4ed7:	2d 4d 3e             	sub    $0x3e4d,%ax
    4eda:	20 66 6f             	and    %ah,0x6f(%bp)
    4edd:	72 20                	jb     0x4eff
    4edf:	42                   	inc    %dx
    4ee0:	49                   	dec    %cx
    4ee1:	4f                   	dec    %di
    4ee2:	53                   	push   %bx
    4ee3:	20 6f 70             	and    %ch,0x70(%bx)
    4ee6:	74 69                	je     0x4f51
    4ee8:	6f                   	outsw  %ds:(%si),(%dx)
    4ee9:	6e                   	outsb  %ds:(%si),(%dx)
    4eea:	73 00                	jae    0x4eec
    4eec:	0d 0a 42             	or     $0x420a,%ax
    4eef:	6f                   	outsw  %ds:(%si),(%dx)
    4ef0:	6f                   	outsw  %ds:(%si),(%dx)
    4ef1:	74 69                	je     0x4f5c
    4ef3:	6e                   	outsb  %ds:(%si),(%dx)
    4ef4:	67 20 66 72          	and    %ah,0x72(%esi)
    4ef8:	6f                   	outsw  %ds:(%si),(%dx)
    4ef9:	6d                   	insw   (%dx),%es:(%di)
    4efa:	20 43 44             	and    %al,0x44(%bp,%di)
    4efd:	2d 52 4f             	sub    $0x4f52,%ax
    4f00:	4d                   	dec    %bp
    4f01:	20 61 73             	and    %ah,0x73(%bx,%di)
    4f04:	20 64 72             	and    %ah,0x72(%si)
    4f07:	69 76 65 20 43       	imul   $0x4320,0x65(%bp),%si
    4f0c:	3a 0d                	cmp    (%di),%cl
    4f0e:	0a 50 72             	or     0x72(%bx,%si),%dl
    4f11:	65 76 69             	gs jbe 0x4f7d
    4f14:	6f                   	outsw  %ds:(%si),(%dx)
    4f15:	75 73                	jne    0x4f8a
    4f17:	6c                   	insb   (%dx),%es:(%di)
    4f18:	79 20                	jns    0x4f3a
    4f1a:	64 65 74 65          	fs gs je 0x4f83
    4f1e:	63 74 65             	arpl   %si,0x65(%si)
    4f21:	64 20 64 72          	and    %ah,%fs:0x72(%si)
    4f25:	69 76 65 73 20       	imul   $0x2073,0x65(%bp),%si
    4f2a:	61                   	popa   
    4f2b:	72 65                	jb     0x4f92
    4f2d:	20 73 68             	and    %dh,0x68(%bp,%di)
    4f30:	69 66 74 65 64       	imul   $0x6465,0x74(%bp),%sp
    4f35:	20 75 70             	and    %dh,0x70(%di)
    4f38:	20 6f 6e             	and    %ch,0x6e(%bx)
    4f3b:	65 20 6c 65          	and    %ch,%gs:0x65(%si)
    4f3f:	74 74                	je     0x4fb5
    4f41:	65 72 00             	gs jb  0x4f44
    4f44:	20 43 44             	and    %al,0x44(%bp,%di)
    4f47:	52                   	push   %dx
    4f48:	4f                   	dec    %di
    4f49:	4d                   	dec    %bp
    4f4a:	20 62 6f             	and    %ah,0x6f(%bp,%si)
    4f4d:	6f                   	outsw  %ds:(%si),(%dx)
    4f4e:	74 20                	je     0x4f70
    4f50:	6d                   	insw   (%dx),%es:(%di)
    4f51:	65 64 69 61 20 69 73 	gs imul $0x7369,%fs:0x20(%bx,%di),%sp
    4f58:	20 6e 6f             	and    %ch,0x6f(%bp)
    4f5b:	74 20                	je     0x4f7d
    4f5d:	73 75                	jae    0x4fd4
    4f5f:	70 70                	jo     0x4fd1
    4f61:	6f                   	outsw  %ds:(%si),(%dx)
    4f62:	72 74                	jb     0x4fd8
    4f64:	65 64 00 45 6e       	gs add %al,%fs:0x6e(%di)
    4f69:	74 65                	je     0x4fd0
    4f6b:	72 20                	jb     0x4f8d
    4f6d:	28 31                	sub    %dh,(%bx,%di)
    4f6f:	20 2d                	and    %ch,(%di)
    4f71:	20 00                	and    %al,(%bx,%si)
    4f73:	29 20                	sub    %sp,(%bx,%si)
    4f75:	3a 00                	cmp    (%bx,%si),%al
    4f77:	45                   	inc    %bp
    4f78:	6e                   	outsb  %ds:(%si),(%dx)
    4f79:	74 65                	je     0x4fe0
    4f7b:	72 20                	jb     0x4f9d
    4f7d:	28 31                	sub    %dh,(%bx,%di)
    4f7f:	20 2d                	and    %ch,(%di)
    4f81:	20 00                	and    %al,(%bx,%si)
    4f83:	29 3b                	sub    %di,(%bp,%di)
    4f85:	20 3c                	and    %bh,(%si)
    4f87:	45                   	inc    %bp
    4f88:	53                   	push   %bx
    4f89:	43                   	inc    %bx
    4f8a:	3e 20 74 6f          	and    %dh,%ds:0x6f(%si)
    4f8e:	20 72 65             	and    %dh,0x65(%bp,%si)
    4f91:	74 75                	je     0x5008
    4f93:	72 6e                	jb     0x5003
    4f95:	20 74 6f             	and    %dh,0x6f(%si)
    4f98:	20 65 6e             	and    %ah,0x6e(%di)
    4f9b:	74 72                	je     0x500f
    4f9d:	69 65 73 20 6d       	imul   $0x6d20,0x73(%di),%sp
    4fa2:	65 6e                	outsb  %gs:(%si),(%dx)
    4fa4:	75 20                	jne    0x4fc6
    4fa6:	3a 00                	cmp    (%bx,%si),%al
    4fa8:	0d 0a 0a             	or     $0xa0a,%ax
    4fab:	41                   	inc    %cx
    4fac:	76 61                	jbe    0x500f
    4fae:	69 6c 61 62 6c       	imul   $0x6c62,0x61(%si),%bp
    4fb3:	65 20 69 6d          	and    %ch,%gs:0x6d(%bx,%di)
    4fb7:	61                   	popa   
    4fb8:	67 65 73 20          	addr32 gs jae 0x4fdc
    4fbc:	66 6f                	outsl  %ds:(%si),(%dx)
    4fbe:	72 20                	jb     0x4fe0
    4fc0:	74 68                	je     0x502a
    4fc2:	69 73 20 65 6e       	imul   $0x6e65,0x20(%bp,%di),%si
    4fc7:	74 72                	je     0x503b
    4fc9:	79 20                	jns    0x4feb
    4fcb:	3a 0d                	cmp    (%di),%cl
    4fcd:	0a 00                	or     (%bx,%si),%al
    4fcf:	0d 0a 42             	or     $0x420a,%ax
    4fd2:	6f                   	outsw  %ds:(%si),(%dx)
    4fd3:	6f                   	outsw  %ds:(%si),(%dx)
    4fd4:	74 61                	je     0x5037
    4fd6:	62 6c 65             	bound  %bp,0x65(%si)
    4fd9:	20 43 44             	and    %al,0x44(%bp,%di)
    4fdc:	2d 52 4f             	sub    $0x4f52,%ax
    4fdf:	4d                   	dec    %bp
    4fe0:	20 69 73             	and    %ch,0x73(%bx,%di)
    4fe3:	20 64 65             	and    %ah,0x65(%si)
    4fe6:	74 65                	je     0x504d
    4fe8:	63 74 65             	arpl   %si,0x65(%si)
    4feb:	64 00 0d             	add    %cl,%fs:(%di)
    4fee:	0a 4d 75             	or     0x75(%di),%cl
    4ff1:	6c                   	insb   (%dx),%es:(%di)
    4ff2:	74 69                	je     0x505d
    4ff4:	2d 68 65             	sub    $0x6568,%ax
    4ff7:	61                   	popa   
    4ff8:	64 65 72 20          	fs gs jb 0x501c
    4ffc:	62 6f 6f             	bound  %bp,0x6f(%bx)
    4fff:	74 61                	je     0x5062
    5001:	62 6c 65             	bound  %bp,0x65(%si)
    5004:	20 65 6e             	and    %ah,0x6e(%di)
    5007:	74 72                	je     0x507b
    5009:	69 65 73 20 61       	imul   $0x6120,0x73(%di),%sp
    500e:	76 61                	jbe    0x5071
    5010:	69 6c 61 62 6c       	imul   $0x6c62,0x61(%si),%bp
    5015:	65 0d 0a 00          	gs or  $0xa,%ax
    5019:	0d 0a 53             	or     $0x530a,%ax
    501c:	69 6e 67 6c 65       	imul   $0x656c,0x67(%bp),%bp
    5021:	20 68 65             	and    %ch,0x65(%bx,%si)
    5024:	61                   	popa   
    5025:	64 65 72 20          	fs gs jb 0x5049
    5029:	62 6f 6f             	bound  %bp,0x6f(%bx)
    502c:	74 20                	je     0x504e
    502e:	65 6e                	outsb  %gs:(%si),(%dx)
    5030:	74 72                	je     0x50a4
    5032:	79 20                	jns    0x5054
    5034:	66 6f                	outsl  %ds:(%si),(%dx)
    5036:	75 6e                	jne    0x50a6
    5038:	64 0d 0a 00          	fs or  $0xa,%ax
    503c:	31 2e 20 44          	xor    %bp,0x4420
    5040:	45                   	inc    %bp
    5041:	46                   	inc    %si
    5042:	41                   	inc    %cx
    5043:	55                   	push   %bp
    5044:	4c                   	dec    %sp
    5045:	54                   	push   %sp
    5046:	20 45 4e             	and    %al,0x4e(%di)
    5049:	54                   	push   %sp
    504a:	52                   	push   %dx
    504b:	59                   	pop    %cx
    504c:	20 20                	and    %ah,(%bx,%si)
    504e:	0d 0a 00             	or     $0xa,%ax
    5051:	0d 0a 07             	or     $0x70a,%ax
    5054:	54                   	push   %sp
    5055:	68 65 20             	push   $0x2065
    5058:	73 79                	jae    0x50d3
    505a:	73 74                	jae    0x50d0
    505c:	65 6d                	gs insw (%dx),%es:(%di)
    505e:	20 42 49             	and    %al,0x49(%bp,%si)
    5061:	4f                   	dec    %di
    5062:	53                   	push   %bx
    5063:	20 64 6f             	and    %ah,0x6f(%si)
    5066:	65 73 20             	gs jae 0x5089
    5069:	6e                   	outsb  %ds:(%si),(%dx)
    506a:	6f                   	outsw  %ds:(%si),(%dx)
    506b:	74 20                	je     0x508d
    506d:	73 75                	jae    0x50e4
    506f:	70 70                	jo     0x50e1
    5071:	6f                   	outsw  %ds:(%si),(%dx)
    5072:	72 74                	jb     0x50e8
    5074:	20 58 42             	and    %bl,0x42(%bx,%si)
    5077:	44                   	inc    %sp
    5078:	41                   	inc    %cx
    5079:	0d 0a 44             	or     $0x440a,%ax
    507c:	41                   	inc    %cx
    507d:	43                   	inc    %bx
    507e:	39 36 30 20          	cmp    %si,0x2030
    5082:	42                   	inc    %dx
    5083:	49                   	dec    %cx
    5084:	4f                   	dec    %di
    5085:	53                   	push   %bx
    5086:	20 64 69             	and    %ah,0x69(%si)
    5089:	73 61                	jae    0x50ec
    508b:	62 6c 65             	bound  %bp,0x65(%si)
    508e:	64 00 44 41          	add    %al,%fs:0x41(%si)
    5092:	43                   	inc    %bx
    5093:	39 36 30 50          	cmp    %si,0x5030
    5097:	4c                   	dec    %sp
    5098:	00 44 41             	add    %al,0x41(%si)
    509b:	43                   	inc    %bx
    509c:	39 36 30 50          	cmp    %si,0x5030
    50a0:	2f                   	das    
    50a1:	50                   	push   %ax
    50a2:	44                   	inc    %sp
    50a3:	00 44 41             	add    %al,0x41(%si)
    50a6:	43                   	inc    %bx
    50a7:	39 36 30 50          	cmp    %si,0x5030
    50ab:	47                   	inc    %di
    50ac:	00 44 41             	add    %al,0x41(%si)
    50af:	43                   	inc    %bx
    50b0:	39 36 30 50          	cmp    %si,0x5030
    50b4:	4a                   	dec    %dx
    50b5:	00 44 41             	add    %al,0x41(%si)
    50b8:	43                   	inc    %bx
    50b9:	39 36 30 50          	cmp    %si,0x5030
    50bd:	52                   	push   %dx
    50be:	00 44 41             	add    %al,0x41(%si)
    50c1:	43                   	inc    %bx
    50c2:	39 36 30 50          	cmp    %si,0x5030
    50c6:	54                   	push   %sp
    50c7:	00 44 41             	add    %al,0x41(%si)
    50ca:	43                   	inc    %bx
    50cb:	39 36 30 50          	cmp    %si,0x5030
    50cf:	54                   	push   %sp
    50d0:	4c                   	dec    %sp
    50d1:	30 00                	xor    %al,(%bx,%si)
    50d3:	44                   	inc    %sp
    50d4:	41                   	inc    %cx
    50d5:	43                   	inc    %bx
    50d6:	39 36 30 50          	cmp    %si,0x5030
    50da:	54                   	push   %sp
    50db:	4c                   	dec    %sp
    50dc:	31 00                	xor    %ax,(%bx,%si)
    50de:	44                   	inc    %sp
    50df:	41                   	inc    %cx
    50e0:	43                   	inc    %bx
    50e1:	39 36 30 50          	cmp    %si,0x5030
    50e5:	52                   	push   %dx
    50e6:	4c                   	dec    %sp
    50e7:	00 44 41             	add    %al,0x41(%si)
    50ea:	43                   	inc    %bx
    50eb:	31 31                	xor    %si,(%bx,%di)
    50ed:	36 34 50             	ss xor $0x50,%al
    50f0:	00 20                	add    %ah,(%bx,%si)
    50f2:	46                   	inc    %si
    50f3:	69 72 6d 77 61       	imul   $0x6177,0x6d(%bp,%si),%si
    50f8:	72 65                	jb     0x515f
    50fa:	20 56 65             	and    %dl,0x65(%bp)
    50fd:	72 73                	jb     0x5172
    50ff:	69 6f 6e 20 00       	imul   $0x20,0x6e(%bx),%bp
    5104:	20 20                	and    %ah,(%bx,%si)
    5106:	20 20                	and    %ah,(%bx,%si)
    5108:	20 4a 61             	and    %cl,0x61(%bp,%si)
    510b:	6e                   	outsb  %ds:(%si),(%dx)
    510c:	20 46 65             	and    %al,0x65(%bp)
    510f:	62 20                	bound  %sp,(%bx,%si)
    5111:	4d                   	dec    %bp
    5112:	61                   	popa   
    5113:	72 20                	jb     0x5135
    5115:	41                   	inc    %cx
    5116:	70 72                	jo     0x518a
    5118:	20 4d 61             	and    %cl,0x61(%di)
    511b:	79 20                	jns    0x513d
    511d:	4a                   	dec    %dx
    511e:	75 6e                	jne    0x518e
    5120:	20 4a 75             	and    %cl,0x75(%bp,%si)
    5123:	6c                   	insb   (%dx),%es:(%di)
    5124:	20 41 75             	and    %al,0x75(%bx,%di)
    5127:	67 20 53 65          	and    %dl,0x65(%ebx)
    512b:	70 20                	jo     0x514d
    512d:	4f                   	dec    %di
    512e:	63 74 20             	arpl   %si,0x20(%si)
    5131:	4e                   	dec    %si
    5132:	6f                   	outsw  %ds:(%si),(%dx)
    5133:	76 20                	jbe    0x5155
    5135:	44                   	inc    %sp
    5136:	65 63 0d             	arpl   %cx,%gs:(%di)
    5139:	0a 44 41             	or     0x41(%si),%al
    513c:	43                   	inc    %bx
    513d:	39 36 30 20          	cmp    %si,0x2030
    5141:	66 6f                	outsl  %ds:(%si),(%dx)
    5143:	75 6e                	jne    0x51b3
    5145:	64 20 6e 65          	and    %ch,%fs:0x65(%bp)
    5149:	77 20                	ja     0x516b
    514b:	63 6f 6e             	arpl   %bp,0x6e(%bx)
    514e:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    5155:	69 
    5156:	6f                   	outsw  %ds:(%si),(%dx)
    5157:	6e                   	outsb  %ds:(%si),(%dx)
    5158:	2c 20                	sub    $0x20,%al
    515a:	69 74 20 77 69       	imul   $0x6977,0x20(%si),%si
    515f:	6c                   	insb   (%dx),%es:(%di)
    5160:	6c                   	insb   (%dx),%es:(%di)
    5161:	20 72 65             	and    %dh,0x65(%bp,%si)
    5164:	73 65                	jae    0x51cb
    5166:	74 20                	je     0x5188
    5168:	74 6f                	je     0x51d9
    516a:	20 75 70             	and    %dh,0x70(%di)
    516d:	64 61                	fs popa 
    516f:	74 65                	je     0x51d6
    5171:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    5174:	6e                   	outsb  %ds:(%si),(%dx)
    5175:	66 69 67 75 72 61 74 	imul   $0x69746172,0x75(%bx),%esp
    517c:	69 
    517d:	6f                   	outsw  %ds:(%si),(%dx)
    517e:	6e                   	outsb  %ds:(%si),(%dx)
    517f:	00 0d                	add    %cl,(%di)
    5181:	0a 44 41             	or     0x41(%si),%al
    5184:	43                   	inc    %bx
    5185:	39 36 30 20          	cmp    %si,0x2030
    5189:	52                   	push   %dx
    518a:	65 73 65             	gs jae 0x51f2
    518d:	74 20                	je     0x51af
    518f:	63 6f 6d             	arpl   %bp,0x6d(%bx)
    5192:	70 6c                	jo     0x5200
    5194:	65 74 65             	gs je  0x51fc
    5197:	00 0d                	add    %cl,(%di)
    5199:	0a 53 63             	or     0x63(%bp,%di),%dl
    519c:	61                   	popa   
    519d:	6e                   	outsb  %ds:(%si),(%dx)
    519e:	6e                   	outsb  %ds:(%si),(%dx)
    519f:	69 6e 67 20 66       	imul   $0x6620,0x67(%bp),%bp
    51a4:	6f                   	outsw  %ds:(%si),(%dx)
    51a5:	72 20                	jb     0x51c7
    51a7:	62 6f 6f             	bound  %bp,0x6f(%bx)
    51aa:	74 61                	je     0x520d
    51ac:	62 6c 65             	bound  %bp,0x65(%si)
    51af:	20 43 44             	and    %al,0x44(%bp,%di)
    51b2:	2d 52 4f             	sub    $0x4f52,%ax
    51b5:	4d                   	dec    %bp
    51b6:	00 0d                	add    %cl,(%di)
    51b8:	0a 46 6f             	or     0x6f(%bp),%al
    51bb:	75 6e                	jne    0x522b
    51bd:	64 20 43 44          	and    %al,%fs:0x44(%bp,%di)
    51c1:	2d 52 4f             	sub    $0x4f52,%ax
    51c4:	4d                   	dec    %bp
    51c5:	20 44 72             	and    %al,0x72(%si)
    51c8:	69 76 65 20 61       	imul   $0x6120,0x65(%bp),%si
    51cd:	74 20                	je     0x51ef
    51cf:	43                   	inc    %bx
    51d0:	68 61 6e             	push   $0x6e61
    51d3:	6e                   	outsb  %ds:(%si),(%dx)
    51d4:	65 6c                	gs insb (%dx),%es:(%di)
    51d6:	3d 00 20             	cmp    $0x2000,%ax
    51d9:	54                   	push   %sp
    51da:	61                   	popa   
    51db:	72 67                	jb     0x5244
    51dd:	65 74 3d             	gs je  0x521d
    51e0:	00 0d                	add    %cl,(%di)
    51e2:	0a 0a                	or     (%bp,%si),%cl
    51e4:	44                   	inc    %sp
    51e5:	41                   	inc    %cx
    51e6:	43                   	inc    %bx
    51e7:	39 36 30 20          	cmp    %si,0x2030
    51eb:	73 63                	jae    0x5250
    51ed:	61                   	popa   
    51ee:	6e                   	outsb  %ds:(%si),(%dx)
    51ef:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    51f2:	6d                   	insw   (%dx),%es:(%di)
    51f3:	70 6c                	jo     0x5261
    51f5:	65 74 65             	gs je  0x525d
    51f8:	64 0d 0a 00          	fs or  $0xa,%ax
    51fc:	0d 0a 41             	or     $0x410a,%ax
    51ff:	45                   	inc    %bp
    5200:	4d                   	dec    %bp
    5201:	49                   	dec    %cx
    5202:	20 73 63             	and    %dh,0x63(%bp,%di)
    5205:	61                   	popa   
    5206:	6e                   	outsb  %ds:(%si),(%dx)
    5207:	6e                   	outsb  %ds:(%si),(%dx)
    5208:	69 6e 67 2c 20       	imul   $0x202c,0x67(%bp),%bp
    520d:	70 6c                	jo     0x527b
    520f:	65 61                	gs popa 
    5211:	73 65                	jae    0x5278
    5213:	20 77 61             	and    %dh,0x61(%bx)
    5216:	69 74 20 2e 2e       	imul   $0x2e2e,0x20(%si),%si
    521b:	2e 20 00             	and    %al,%cs:(%bx,%si)
    521e:	20 42 75             	and    %al,0x75(%bp,%si)
    5221:	69 6c 64 20 00       	imul   $0x20,0x64(%si),%bp
    5226:	0d 0a 3c             	or     $0x3c0a,%ax
    5229:	46                   	inc    %si
    522a:	4f                   	dec    %di
    522b:	52                   	push   %dx
    522c:	20 45 56             	and    %al,0x56(%di)
    522f:	41                   	inc    %cx
    5230:	4c                   	dec    %sp
    5231:	55                   	push   %bp
    5232:	41                   	inc    %cx
    5233:	54                   	push   %sp
    5234:	49                   	dec    %cx
    5235:	4f                   	dec    %di
    5236:	4e                   	dec    %si
    5237:	20 4f 4e             	and    %cl,0x4e(%bx)
    523a:	4c                   	dec    %sp
    523b:	59                   	pop    %cx
    523c:	3e 00 0d             	add    %cl,%ds:(%di)
    523f:	0a 07                	or     (%bx),%al
    5241:	44                   	inc    %sp
    5242:	41                   	inc    %cx
    5243:	43                   	inc    %bx
    5244:	39 36 30 20          	cmp    %si,0x2030
    5248:	69 73 20 6e 6f       	imul   $0x6f6e,0x20(%bp,%di),%si
    524d:	74 20                	je     0x526f
    524f:	72 65                	jb     0x52b6
    5251:	73 70                	jae    0x52c3
    5253:	6f                   	outsw  %ds:(%si),(%dx)
    5254:	6e                   	outsb  %ds:(%si),(%dx)
    5255:	64 69 6e 67 20 28    	imul   $0x2820,%fs:0x67(%bp),%bp
    525b:	4d                   	dec    %bp
    525c:	41                   	inc    %cx
    525d:	49                   	dec    %cx
    525e:	4c                   	dec    %sp
    525f:	20 42 4f             	and    %al,0x4f(%bp,%si)
    5262:	58                   	pop    %ax
    5263:	20 46 55             	and    %al,0x55(%bp)
    5266:	4c                   	dec    %sp
    5267:	4c                   	dec    %sp
    5268:	29 00                	sub    %ax,(%bx,%si)
    526a:	0d 0a 41             	or     $0x410a,%ax
    526d:	6c                   	insb   (%dx),%es:(%di)
    526e:	74 65                	je     0x52d5
    5270:	72 6e                	jb     0x52e0
    5272:	61                   	popa   
    5273:	74 65                	je     0x52da
    5275:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    5278:	6e                   	outsb  %ds:(%si),(%dx)
    5279:	73 6f                	jae    0x52ea
    527b:	6c                   	insb   (%dx),%es:(%di)
    527c:	65 20 73 65          	and    %dh,%gs:0x65(%bp,%di)
    5280:	6c                   	insb   (%dx),%es:(%di)
    5281:	65 63 74 69          	arpl   %si,%gs:0x69(%si)
    5285:	6f                   	outsw  %ds:(%si),(%dx)
    5286:	6e                   	outsb  %ds:(%si),(%dx)
    5287:	3a 20                	cmp    (%bx,%si),%ah
    5289:	50                   	push   %ax
    528a:	72 65                	jb     0x52f1
    528c:	73 73                	jae    0x5301
    528e:	20 6e 75             	and    %ch,0x75(%bp)
    5291:	6d                   	insw   (%dx),%es:(%di)
    5292:	62 65 72             	bound  %sp,0x72(%di)
    5295:	0d 0a 30             	or     $0x300a,%ax
    5298:	2d 33 20             	sub    $0x2033,%ax
    529b:	66 6f                	outsl  %ds:(%si),(%dx)
    529d:	72 20                	jb     0x52bf
    529f:	63 6f 6d             	arpl   %bp,0x6d(%bx)
    52a2:	6d                   	insw   (%dx),%es:(%di)
    52a3:	75 6e                	jne    0x5313
    52a5:	69 63 61 74 69       	imul   $0x6974,0x61(%bp,%di),%sp
    52aa:	6f                   	outsw  %ds:(%si),(%dx)
    52ab:	6e                   	outsb  %ds:(%si),(%dx)
    52ac:	20 70 6f             	and    %dh,0x6f(%bx,%si)
    52af:	72 74                	jb     0x5325
    52b1:	20 30                	and    %dh,(%bx,%si)
    52b3:	2d 33 20             	sub    $0x2033,%ax
    52b6:	61                   	popa   
    52b7:	6e                   	outsb  %ds:(%si),(%dx)
    52b8:	64 20 56 47          	and    %dl,%fs:0x47(%bp)
    52bc:	41                   	inc    %cx
    52bd:	0d 0a 34             	or     $0x340a,%ax
    52c0:	2d 37 20             	sub    $0x2037,%ax
    52c3:	66 6f                	outsl  %ds:(%si),(%dx)
    52c5:	72 20                	jb     0x52e7
    52c7:	63 6f 6d             	arpl   %bp,0x6d(%bx)
    52ca:	6d                   	insw   (%dx),%es:(%di)
    52cb:	75 6e                	jne    0x533b
    52cd:	69 63 61 74 69       	imul   $0x6974,0x61(%bp,%di),%sp
    52d2:	6f                   	outsw  %ds:(%si),(%dx)
    52d3:	6e                   	outsb  %ds:(%si),(%dx)
    52d4:	20 70 6f             	and    %dh,0x6f(%bx,%si)
    52d7:	72 74                	jb     0x534d
    52d9:	20 30                	and    %dh,(%bx,%si)
    52db:	2d 33 20             	sub    $0x2033,%ax
    52de:	6f                   	outsw  %ds:(%si),(%dx)
    52df:	6e                   	outsb  %ds:(%si),(%dx)
    52e0:	6c                   	insb   (%dx),%es:(%di)
    52e1:	79 0d                	jns    0x52f0
    52e3:	0a 54 68             	or     0x68(%si),%dl
    52e6:	65 20 63 6f          	and    %ah,%gs:0x6f(%bp,%di)
    52ea:	6d                   	insw   (%dx),%es:(%di)
    52eb:	6d                   	insw   (%dx),%es:(%di)
    52ec:	20 70 6f             	and    %dh,0x6f(%bx,%si)
    52ef:	72 74                	jb     0x5365
    52f1:	20 63 6f             	and    %ah,0x6f(%bp,%di)
    52f4:	6e                   	outsb  %ds:(%si),(%dx)
    52f5:	66 69 67 72 61 74 69 	imul   $0x6f697461,0x72(%bx),%esp
    52fc:	6f 
    52fd:	6e                   	outsb  %ds:(%si),(%dx)
    52fe:	20 69 73             	and    %ch,0x73(%bx,%di)
    5301:	20 39                	and    %bh,(%bx,%di)
    5303:	36 30 30             	xor    %dh,%ss:(%bx,%si)
    5306:	20 62 61             	and    %ah,0x61(%bp,%si)
    5309:	75 64                	jne    0x536f
    530b:	2c 20                	sub    $0x20,%al
    530d:	31 73 74             	xor    %si,0x74(%bp,%di)
    5310:	6f                   	outsw  %ds:(%si),(%dx)
    5311:	70 20                	jo     0x5333
    5313:	62 69 74             	bound  %bp,0x74(%bx,%di)
    5316:	2c 20                	sub    $0x20,%al
    5318:	38 62 69             	cmp    %ah,0x69(%bp,%si)
    531b:	74 20                	je     0x533d
    531d:	64 61                	fs popa 
    531f:	74 61                	je     0x5382
    5321:	2c 20                	sub    $0x20,%al
    5323:	6e                   	outsb  %ds:(%si),(%dx)
    5324:	6f                   	outsw  %ds:(%si),(%dx)
    5325:	20 70 61             	and    %dh,0x61(%bx,%si)
    5328:	72 69                	jb     0x5393
    532a:	74 79                	je     0x53a5
    532c:	0d 0a 00             	or     $0xa,%ax
    532f:	0d 0a 07             	or     $0x70a,%ax
    5332:	44                   	inc    %sp
    5333:	41                   	inc    %cx
    5334:	43                   	inc    %bx
    5335:	39 36 30 3a          	cmp    %si,0x3a30
    5339:	20 45 72             	and    %al,0x72(%di)
    533c:	72 6f                	jb     0x53ad
    533e:	72 20                	jb     0x5360
    5340:	69 6e 20 73 79       	imul   $0x7973,0x20(%bp),%bp
    5345:	73 74                	jae    0x53bb
    5347:	65 6d                	gs insw (%dx),%es:(%di)
    5349:	20 42 49             	and    %al,0x49(%bp,%si)
    534c:	4f                   	dec    %di
    534d:	53                   	push   %bx
    534e:	20 50 43             	and    %dl,0x43(%bx,%si)
    5351:	49                   	dec    %cx
    5352:	20 73 65             	and    %dh,0x65(%bp,%di)
    5355:	72 76                	jb     0x53cd
    5357:	69 63 65 20 63       	imul   $0x6320,0x65(%bp,%di),%sp
    535c:	61                   	popa   
    535d:	6c                   	insb   (%dx),%es:(%di)
    535e:	6c                   	insb   (%dx),%es:(%di)
    535f:	20 2d                	and    %ch,(%di)
    5361:	20 0d                	and    %cl,(%di)
    5363:	0a 00                	or     (%bx,%si),%al
    5365:	0d 0a 44             	or     $0x440a,%ax
    5368:	41                   	inc    %cx
    5369:	43                   	inc    %bx
    536a:	39 36 30 20          	cmp    %si,0x2030
    536e:	50                   	push   %ax
    536f:	43                   	inc    %bx
    5370:	49                   	dec    %cx
    5371:	20 41 64             	and    %al,0x64(%bx,%di)
    5374:	64 72 65             	fs jb  0x53dc
    5377:	73 73                	jae    0x53ec
    5379:	3a 20                	cmp    (%bx,%si),%ah
    537b:	00 20                	add    %ah,(%bx,%si)
    537d:	42                   	inc    %dx
    537e:	75 73                	jne    0x53f3
    5380:	3d 00 20             	cmp    $0x2000,%ax
    5383:	44                   	inc    %sp
    5384:	65 76 2f             	gs jbe 0x53b6
    5387:	53                   	push   %bx
    5388:	6c                   	insb   (%dx),%es:(%di)
    5389:	6f                   	outsw  %ds:(%si),(%dx)
    538a:	74 3d                	je     0x53c9
    538c:	00 20                	add    %ah,(%bx,%si)
    538e:	46                   	inc    %si
    538f:	75 6e                	jne    0x53ff
    5391:	63 74 69             	arpl   %si,0x69(%si)
    5394:	6f                   	outsw  %ds:(%si),(%dx)
    5395:	6e                   	outsb  %ds:(%si),(%dx)
    5396:	3d 00 20             	cmp    $0x2000,%ax
    5399:	49                   	dec    %cx
    539a:	52                   	push   %dx
    539b:	51                   	push   %cx
    539c:	3d 00 0d             	cmp    $0xd00,%ax
    539f:	0a 44 6f             	or     0x6f(%si),%al
    53a2:	20 79 6f             	and    %bh,0x6f(%bx,%di)
    53a5:	75 20                	jne    0x53c7
    53a7:	77 61                	ja     0x540a
    53a9:	6e                   	outsb  %ds:(%si),(%dx)
    53aa:	74 20                	je     0x53cc
    53ac:	74 6f                	je     0x541d
    53ae:	20 62 79             	and    %ah,0x79(%bp,%si)
    53b1:	70 61                	jo     0x5414
    53b3:	73 73                	jae    0x5428
    53b5:	20 43 44             	and    %al,0x44(%bp,%di)
    53b8:	2d 52 4f             	sub    $0x4f52,%ax
    53bb:	4d                   	dec    %bp
    53bc:	20 62 6f             	and    %ah,0x6f(%bp,%si)
    53bf:	6f                   	outsw  %ds:(%si),(%dx)
    53c0:	74 20                	je     0x53e2
    53c2:	5b                   	pop    %bx
    53c3:	79 2f                	jns    0x53f4
    53c5:	6e                   	outsb  %ds:(%si),(%dx)
    53c6:	5d                   	pop    %bp
    53c7:	20 3f                	and    %bh,(%bx)
    53c9:	00 0d                	add    %cl,(%di)
    53cb:	0a 43 44             	or     0x44(%bp,%di),%al
    53ce:	2d 52 4f             	sub    $0x4f52,%ax
    53d1:	4d                   	dec    %bp
    53d2:	20 62 6f             	and    %ah,0x6f(%bp,%si)
    53d5:	6f                   	outsw  %ds:(%si),(%dx)
    53d6:	74 20                	je     0x53f8
    53d8:	62 79 70             	bound  %di,0x70(%bx,%di)
    53db:	61                   	popa   
    53dc:	73 73                	jae    0x5451
    53de:	65 64 00 20          	gs add %ah,%fs:(%bx,%si)
    53e2:	28 43 44             	sub    %al,0x44(%bp,%di)
    53e5:	2d 52 4f             	sub    $0x4f52,%ax
    53e8:	4d                   	dec    %bp
    53e9:	29 00                	sub    %ax,(%bx,%si)
    53eb:	20 28                	and    %ch,(%bx,%si)
    53ed:	31 2e 32 20          	xor    %bp,0x2032
    53f1:	4d                   	dec    %bp
    53f2:	42                   	inc    %dx
    53f3:	20 44 69             	and    %al,0x69(%si)
    53f6:	73 6b                	jae    0x5463
    53f8:	65 74 74             	gs je  0x546f
    53fb:	65 29 00             	sub    %ax,%gs:(%bx,%si)
    53fe:	20 28                	and    %ch,(%bx,%si)
    5400:	31 2e 34 34          	xor    %bp,0x3434
    5404:	20 4d 42             	and    %cl,0x42(%di)
    5407:	20 44 69             	and    %al,0x69(%si)
    540a:	73 6b                	jae    0x5477
    540c:	65 74 74             	gs je  0x5483
    540f:	65 29 00             	sub    %ax,%gs:(%bx,%si)
    5412:	20 28                	and    %ch,(%bx,%si)
    5414:	32 2e 38 38          	xor    0x3838,%ch
    5418:	20 4d 42             	and    %cl,0x42(%di)
    541b:	20 44 69             	and    %al,0x69(%si)
    541e:	73 6b                	jae    0x548b
    5420:	65 74 74             	gs je  0x5497
    5423:	65 29 00             	sub    %ax,%gs:(%bx,%si)
    5426:	20 28                	and    %ch,(%bx,%si)
    5428:	48                   	dec    %ax
    5429:	61                   	popa   
    542a:	72 64                	jb     0x5490
    542c:	20 44 69             	and    %al,0x69(%si)
    542f:	73 6b                	jae    0x549c
    5431:	29 00                	sub    %ax,(%bx,%si)
    5433:	20 28                	and    %ch,(%bx,%si)
    5435:	29 00                	sub    %ax,(%bx,%si)
    5437:	e1 53                	loope  0x548c
    5439:	eb 53                	jmp    0x548e
    543b:	fe                   	(bad)  
    543c:	53                   	push   %bx
    543d:	12 54 26             	adc    0x26(%si),%dl
    5440:	54                   	push   %sp
    5441:	33 54 33             	xor    0x33(%si),%dx
    5444:	54                   	push   %sp
    5445:	33 54 33             	xor    0x33(%si),%dx
    5448:	54                   	push   %sp
    5449:	33 54 33             	xor    0x33(%si),%dx
    544c:	54                   	push   %sp
    544d:	33 54 33             	xor    0x33(%si),%dx
    5450:	54                   	push   %sp
    5451:	33 54 33             	xor    0x33(%si),%dx
    5454:	54                   	push   %sp
    5455:	33 54 00             	xor    0x0(%si),%dx
    5458:	00 00                	add    %al,(%bx,%si)
    545a:	00 00                	add    %al,(%bx,%si)
    545c:	f8                   	clc    
    545d:	03 f8                	add    %ax,%di
    545f:	02 e8                	add    %al,%ch
    5461:	03 e8                	add    %ax,%bp
    5463:	02 fd                	add    %ch,%bh
    5465:	03 fd                	add    %bp,%di
    5467:	02 ed                	add    %ch,%ch
    5469:	03 ed                	add    %bp,%bp
    546b:	02 00                	add    (%bx,%si),%al
    546d:	00 00                	add    %al,(%bx,%si)
    546f:	00 00                	add    %al,(%bx,%si)
    5471:	00 00                	add    %al,(%bx,%si)
    5473:	00 8b 16 94          	add    %cl,-0x6bea(%bp,%di)
    5477:	16                   	push   %ss
    5478:	9d                   	popf   
    5479:	16                   	push   %ss
    547a:	a6                   	cmpsb  %es:(%di),%ds:(%si)
    547b:	16                   	push   %ss
    547c:	af                   	scas   %es:(%di),%ax
    547d:	16                   	push   %ss
    547e:	b8 16 c1             	mov    $0xc116,%ax
    5481:	16                   	push   %ss
    5482:	ca 16 d3             	lret   $0xd316
    5485:	16                   	push   %ss
    5486:	dc 16 e5 16          	fcoml  0x16e5
    548a:	ee                   	out    %al,(%dx)
    548b:	16                   	push   %ss
    548c:	f7 16 00 17          	notw   0x1700
    5490:	09 17                	or     %dx,(%bx)
    5492:	12 17                	adc    (%bx),%dl
	...
    549c:	aa                   	stos   %al,%es:(%di)
    549d:	aa                   	stos   %al,%es:(%di)
    549e:	aa                   	stos   %al,%es:(%di)
    549f:	aa                   	stos   %al,%es:(%di)
    54a0:	aa                   	stos   %al,%es:(%di)
    54a1:	aa                   	stos   %al,%es:(%di)
    54a2:	aa                   	stos   %al,%es:(%di)
    54a3:	aa                   	stos   %al,%es:(%di)
    54a4:	aa                   	stos   %al,%es:(%di)
    54a5:	aa                   	stos   %al,%es:(%di)
    54a6:	aa                   	stos   %al,%es:(%di)
    54a7:	aa                   	stos   %al,%es:(%di)
    54a8:	aa                   	stos   %al,%es:(%di)
    54a9:	aa                   	stos   %al,%es:(%di)
    54aa:	aa                   	stos   %al,%es:(%di)
    54ab:	aa                   	stos   %al,%es:(%di)
    54ac:	aa                   	stos   %al,%es:(%di)
    54ad:	aa                   	stos   %al,%es:(%di)
    54ae:	aa                   	stos   %al,%es:(%di)
    54af:	aa                   	stos   %al,%es:(%di)
	...
    5930:	ff                   	(bad)  
    5931:	ff                   	(bad)  
    5932:	ff                   	(bad)  
    5933:	ff                   	(bad)  
    5934:	ff                   	(bad)  
    5935:	ff                   	(bad)  
    5936:	ff                   	(bad)  
    5937:	ff                   	(bad)  
    5938:	ff                   	(bad)  
    5939:	ff                   	(bad)  
    593a:	ff                   	(bad)  
    593b:	ff                   	(bad)  
    593c:	ff                   	(bad)  
    593d:	ff                   	(bad)  
    593e:	ff                   	(bad)  
    593f:	ff                   	(bad)  
    5940:	ff                   	(bad)  
    5941:	ff                   	(bad)  
    5942:	ff                   	(bad)  
    5943:	ff                   	(bad)  
    5944:	ff                   	(bad)  
    5945:	ff                   	(bad)  
    5946:	ff                   	(bad)  
    5947:	ff                   	(bad)  
    5948:	ff                   	(bad)  
    5949:	ff                   	(bad)  
    594a:	ff                   	(bad)  
    594b:	ff                   	(bad)  
    594c:	ff                   	(bad)  
    594d:	ff                   	(bad)  
    594e:	ff                   	(bad)  
    594f:	ff                   	(bad)  
    5950:	ff                   	(bad)  
    5951:	ff                   	(bad)  
    5952:	ff                   	(bad)  
    5953:	ff                   	(bad)  
    5954:	ff                   	(bad)  
    5955:	ff                   	(bad)  
    5956:	ff                   	(bad)  
    5957:	ff                   	(bad)  
    5958:	ff                   	(bad)  
    5959:	ff                   	(bad)  
    595a:	ff                   	(bad)  
    595b:	ff                   	(bad)  
    595c:	ff                   	(bad)  
    595d:	ff                   	(bad)  
    595e:	ff                   	(bad)  
    595f:	ff                   	(bad)  
    5960:	ff                   	(bad)  
    5961:	ff                   	(bad)  
    5962:	ff                   	(bad)  
    5963:	ff                   	(bad)  
    5964:	ff                   	(bad)  
    5965:	ff                   	(bad)  
    5966:	ff                   	(bad)  
    5967:	ff                   	(bad)  
    5968:	ff                   	(bad)  
    5969:	ff                   	(bad)  
    596a:	ff                   	(bad)  
    596b:	ff                   	(bad)  
    596c:	ff                   	(bad)  
    596d:	ff                   	(bad)  
    596e:	ff                   	(bad)  
    596f:	ff                   	(bad)  
    5970:	ff                   	(bad)  
    5971:	ff                   	(bad)  
    5972:	ff                   	(bad)  
    5973:	ff                   	(bad)  
    5974:	ff                   	(bad)  
    5975:	ff                   	(bad)  
    5976:	ff                   	(bad)  
    5977:	ff                   	(bad)  
    5978:	ff                   	(bad)  
    5979:	ff                   	(bad)  
    597a:	ff                   	(bad)  
    597b:	ff                   	(bad)  
    597c:	ff                   	(bad)  
    597d:	ff                   	(bad)  
    597e:	ff                   	(bad)  
    597f:	ff                   	(bad)  
    5980:	ff                   	(bad)  
    5981:	ff                   	(bad)  
    5982:	ff                   	(bad)  
    5983:	ff                   	(bad)  
    5984:	ff                   	(bad)  
    5985:	ff                   	(bad)  
    5986:	ff                   	(bad)  
    5987:	ff                   	(bad)  
    5988:	ff                   	(bad)  
    5989:	ff                   	(bad)  
    598a:	ff                   	(bad)  
    598b:	ff                   	(bad)  
    598c:	ff                   	(bad)  
    598d:	ff                   	(bad)  
    598e:	ff                   	(bad)  
    598f:	ff                   	(bad)  
    5990:	ff                   	(bad)  
    5991:	ff                   	(bad)  
    5992:	ff                   	(bad)  
    5993:	ff                   	(bad)  
    5994:	ff                   	(bad)  
    5995:	ff                   	(bad)  
    5996:	ff                   	(bad)  
    5997:	ff                   	(bad)  
    5998:	ff                   	(bad)  
    5999:	ff                   	(bad)  
    599a:	ff                   	(bad)  
    599b:	ff                   	(bad)  
    599c:	ff                   	(bad)  
    599d:	ff                   	(bad)  
    599e:	ff                   	(bad)  
    599f:	ff                   	(bad)  
    59a0:	ff                   	(bad)  
    59a1:	ff                   	(bad)  
    59a2:	ff                   	(bad)  
    59a3:	ff                   	(bad)  
    59a4:	ff                   	(bad)  
    59a5:	ff                   	(bad)  
    59a6:	ff                   	(bad)  
    59a7:	ff                   	(bad)  
    59a8:	ff                   	(bad)  
    59a9:	ff                   	(bad)  
    59aa:	ff                   	(bad)  
    59ab:	ff                   	(bad)  
    59ac:	ff                   	(bad)  
    59ad:	ff                   	(bad)  
    59ae:	ff                   	(bad)  
    59af:	ff                   	(bad)  
    59b0:	ff                   	(bad)  
    59b1:	ff                   	(bad)  
    59b2:	ff                   	(bad)  
    59b3:	ff                   	(bad)  
    59b4:	ff                   	(bad)  
    59b5:	ff                   	(bad)  
    59b6:	ff                   	(bad)  
    59b7:	ff                   	(bad)  
    59b8:	ff                   	(bad)  
    59b9:	ff                   	(bad)  
    59ba:	ff                   	(bad)  
    59bb:	ff                   	(bad)  
    59bc:	ff                   	(bad)  
    59bd:	ff                   	(bad)  
    59be:	ff                   	(bad)  
    59bf:	ff                   	(bad)  
    59c0:	ff                   	(bad)  
    59c1:	ff                   	(bad)  
    59c2:	ff                   	(bad)  
    59c3:	ff                   	(bad)  
    59c4:	ff                   	(bad)  
    59c5:	ff                   	(bad)  
    59c6:	ff                   	(bad)  
    59c7:	ff                   	(bad)  
    59c8:	ff                   	(bad)  
    59c9:	ff                   	(bad)  
    59ca:	ff                   	(bad)  
    59cb:	ff                   	(bad)  
    59cc:	ff                   	(bad)  
    59cd:	ff                   	(bad)  
    59ce:	ff                   	(bad)  
    59cf:	ff                   	(bad)  
    59d0:	ff                   	(bad)  
    59d1:	ff                   	(bad)  
    59d2:	ff                   	(bad)  
    59d3:	ff                   	(bad)  
    59d4:	ff                   	(bad)  
    59d5:	ff                   	(bad)  
    59d6:	ff                   	(bad)  
    59d7:	ff                   	(bad)  
    59d8:	ff                   	(bad)  
    59d9:	ff                   	(bad)  
    59da:	ff                   	(bad)  
    59db:	ff                   	(bad)  
    59dc:	ff                   	(bad)  
    59dd:	ff                   	(bad)  
    59de:	ff                   	(bad)  
    59df:	ff                   	(bad)  
    59e0:	ff                   	(bad)  
    59e1:	ff                   	(bad)  
    59e2:	ff                   	(bad)  
    59e3:	ff                   	(bad)  
    59e4:	ff                   	(bad)  
    59e5:	ff                   	(bad)  
    59e6:	ff                   	(bad)  
    59e7:	ff                   	(bad)  
    59e8:	ff                   	(bad)  
    59e9:	ff                   	(bad)  
    59ea:	ff                   	(bad)  
    59eb:	ff                   	(bad)  
    59ec:	ff                   	(bad)  
    59ed:	ff                   	(bad)  
    59ee:	ff                   	(bad)  
    59ef:	ff                   	(bad)  
    59f0:	ff                   	(bad)  
    59f1:	ff                   	(bad)  
    59f2:	ff                   	(bad)  
    59f3:	ff                   	(bad)  
    59f4:	ff                   	(bad)  
    59f5:	ff                   	(bad)  
    59f6:	ff                   	(bad)  
    59f7:	ff                   	(bad)  
    59f8:	ff                   	(bad)  
    59f9:	ff                   	(bad)  
    59fa:	ff                   	(bad)  
    59fb:	ff                   	(bad)  
    59fc:	ff                   	(bad)  
    59fd:	ff                   	(bad)  
    59fe:	ff                   	(bad)  
    59ff:	ff                   	(bad)  
    5a00:	ff                   	(bad)  
    5a01:	ff                   	(bad)  
    5a02:	ff                   	(bad)  
    5a03:	ff                   	(bad)  
    5a04:	ff                   	(bad)  
    5a05:	ff                   	(bad)  
    5a06:	ff                   	(bad)  
    5a07:	ff                   	(bad)  
    5a08:	ff                   	(bad)  
    5a09:	ff                   	(bad)  
    5a0a:	ff                   	(bad)  
    5a0b:	ff                   	(bad)  
    5a0c:	ff                   	(bad)  
    5a0d:	ff                   	(bad)  
    5a0e:	ff                   	(bad)  
    5a0f:	ff                   	(bad)  
    5a10:	ff                   	(bad)  
    5a11:	ff                   	(bad)  
    5a12:	ff                   	(bad)  
    5a13:	ff                   	(bad)  
    5a14:	ff                   	(bad)  
    5a15:	ff                   	(bad)  
    5a16:	ff                   	(bad)  
    5a17:	ff                   	(bad)  
    5a18:	ff                   	(bad)  
    5a19:	ff                   	(bad)  
    5a1a:	ff                   	(bad)  
    5a1b:	ff                   	(bad)  
    5a1c:	ff                   	(bad)  
    5a1d:	ff                   	(bad)  
    5a1e:	ff                   	(bad)  
    5a1f:	ff                   	(bad)  
    5a20:	ff                   	(bad)  
    5a21:	ff                   	(bad)  
    5a22:	ff                   	(bad)  
    5a23:	ff                   	(bad)  
    5a24:	ff                   	(bad)  
    5a25:	ff                   	(bad)  
    5a26:	ff                   	(bad)  
    5a27:	ff                   	(bad)  
    5a28:	ff                   	(bad)  
    5a29:	ff                   	(bad)  
    5a2a:	ff                   	(bad)  
    5a2b:	ff                   	(bad)  
    5a2c:	ff                   	(bad)  
    5a2d:	ff                   	(bad)  
    5a2e:	ff                   	(bad)  
    5a2f:	ff                   	(bad)  
    5a30:	ff                   	(bad)  
    5a31:	ff                   	(bad)  
    5a32:	ff                   	(bad)  
    5a33:	ff                   	(bad)  
    5a34:	ff                   	(bad)  
    5a35:	ff                   	(bad)  
    5a36:	ff                   	(bad)  
    5a37:	ff                   	(bad)  
    5a38:	ff                   	(bad)  
    5a39:	ff                   	(bad)  
    5a3a:	ff                   	(bad)  
    5a3b:	ff                   	(bad)  
    5a3c:	ff                   	(bad)  
    5a3d:	ff                   	(bad)  
    5a3e:	ff                   	(bad)  
    5a3f:	ff                   	(bad)  
    5a40:	ff                   	(bad)  
    5a41:	ff                   	(bad)  
    5a42:	ff                   	(bad)  
    5a43:	ff                   	(bad)  
    5a44:	ff                   	(bad)  
    5a45:	ff                   	(bad)  
    5a46:	ff                   	(bad)  
    5a47:	ff                   	(bad)  
    5a48:	ff                   	(bad)  
    5a49:	ff                   	(bad)  
    5a4a:	ff                   	(bad)  
    5a4b:	ff                   	(bad)  
    5a4c:	ff                   	(bad)  
    5a4d:	ff                   	(bad)  
    5a4e:	ff                   	(bad)  
    5a4f:	ff                   	(bad)  
    5a50:	ff                   	(bad)  
    5a51:	ff                   	(bad)  
    5a52:	ff                   	(bad)  
    5a53:	ff                   	(bad)  
    5a54:	ff                   	(bad)  
    5a55:	ff                   	(bad)  
    5a56:	ff                   	(bad)  
    5a57:	ff                   	(bad)  
    5a58:	ff                   	(bad)  
    5a59:	ff                   	(bad)  
    5a5a:	ff                   	(bad)  
    5a5b:	ff                   	(bad)  
    5a5c:	ff                   	(bad)  
    5a5d:	ff                   	(bad)  
    5a5e:	ff                   	(bad)  
    5a5f:	ff                   	(bad)  
    5a60:	ff                   	(bad)  
    5a61:	ff                   	(bad)  
    5a62:	ff                   	(bad)  
    5a63:	ff                   	(bad)  
    5a64:	ff                   	(bad)  
    5a65:	ff                   	(bad)  
    5a66:	ff                   	(bad)  
    5a67:	ff                   	(bad)  
    5a68:	ff                   	(bad)  
    5a69:	ff                   	(bad)  
    5a6a:	ff                   	(bad)  
    5a6b:	ff                   	(bad)  
    5a6c:	ff                   	(bad)  
    5a6d:	ff                   	(bad)  
    5a6e:	ff                   	(bad)  
    5a6f:	ff                   	(bad)  
    5a70:	ff                   	(bad)  
    5a71:	ff                   	(bad)  
    5a72:	ff                   	(bad)  
    5a73:	ff                   	(bad)  
    5a74:	ff                   	(bad)  
    5a75:	ff                   	(bad)  
    5a76:	ff                   	(bad)  
    5a77:	ff                   	(bad)  
    5a78:	ff                   	(bad)  
    5a79:	ff                   	(bad)  
    5a7a:	ff                   	(bad)  
    5a7b:	ff                   	(bad)  
    5a7c:	ff                   	(bad)  
    5a7d:	ff                   	(bad)  
    5a7e:	ff                   	(bad)  
    5a7f:	ff                   	(bad)  
    5a80:	ff                   	(bad)  
    5a81:	ff                   	(bad)  
    5a82:	ff                   	(bad)  
    5a83:	ff                   	(bad)  
    5a84:	ff                   	(bad)  
    5a85:	ff                   	(bad)  
    5a86:	ff                   	(bad)  
    5a87:	ff                   	(bad)  
    5a88:	ff                   	(bad)  
    5a89:	ff                   	(bad)  
    5a8a:	ff                   	(bad)  
    5a8b:	ff                   	(bad)  
    5a8c:	ff                   	(bad)  
    5a8d:	ff                   	(bad)  
    5a8e:	ff                   	(bad)  
    5a8f:	ff                   	(bad)  
    5a90:	ff                   	(bad)  
    5a91:	ff                   	(bad)  
    5a92:	ff                   	(bad)  
    5a93:	ff                   	(bad)  
    5a94:	ff                   	(bad)  
    5a95:	ff                   	(bad)  
    5a96:	ff                   	(bad)  
    5a97:	ff                   	(bad)  
    5a98:	ff                   	(bad)  
    5a99:	ff                   	(bad)  
    5a9a:	ff                   	(bad)  
    5a9b:	ff                   	(bad)  
    5a9c:	ff                   	(bad)  
    5a9d:	ff                   	(bad)  
    5a9e:	ff                   	(bad)  
    5a9f:	ff                   	(bad)  
    5aa0:	ff                   	(bad)  
    5aa1:	ff                   	(bad)  
    5aa2:	ff                   	(bad)  
    5aa3:	ff                   	(bad)  
    5aa4:	ff                   	(bad)  
    5aa5:	ff                   	(bad)  
    5aa6:	ff                   	(bad)  
    5aa7:	ff                   	(bad)  
    5aa8:	ff                   	(bad)  
    5aa9:	ff                   	(bad)  
    5aaa:	ff                   	(bad)  
    5aab:	ff                   	(bad)  
    5aac:	ff                   	(bad)  
    5aad:	ff                   	(bad)  
    5aae:	ff                   	(bad)  
    5aaf:	ff                   	(bad)  
    5ab0:	ff                   	(bad)  
    5ab1:	ff                   	(bad)  
    5ab2:	ff                   	(bad)  
    5ab3:	ff                   	(bad)  
    5ab4:	ff                   	(bad)  
    5ab5:	ff                   	(bad)  
    5ab6:	ff                   	(bad)  
    5ab7:	ff                   	(bad)  
    5ab8:	ff                   	(bad)  
    5ab9:	ff                   	(bad)  
    5aba:	ff                   	(bad)  
    5abb:	ff                   	(bad)  
    5abc:	ff                   	(bad)  
    5abd:	ff                   	(bad)  
    5abe:	ff                   	(bad)  
    5abf:	ff                   	(bad)  
    5ac0:	ff                   	(bad)  
    5ac1:	ff                   	(bad)  
    5ac2:	ff                   	(bad)  
    5ac3:	ff                   	(bad)  
    5ac4:	ff                   	(bad)  
    5ac5:	ff                   	(bad)  
    5ac6:	ff                   	(bad)  
    5ac7:	ff                   	(bad)  
    5ac8:	ff                   	(bad)  
    5ac9:	ff                   	(bad)  
    5aca:	ff                   	(bad)  
    5acb:	ff                   	(bad)  
    5acc:	ff                   	(bad)  
    5acd:	ff                   	(bad)  
    5ace:	ff                   	(bad)  
    5acf:	ff                   	(bad)  
    5ad0:	ff                   	(bad)  
    5ad1:	ff                   	(bad)  
    5ad2:	ff                   	(bad)  
    5ad3:	ff                   	(bad)  
    5ad4:	ff                   	(bad)  
    5ad5:	ff                   	(bad)  
    5ad6:	ff                   	(bad)  
    5ad7:	ff                   	(bad)  
    5ad8:	ff                   	(bad)  
    5ad9:	ff                   	(bad)  
    5ada:	ff                   	(bad)  
    5adb:	ff                   	(bad)  
    5adc:	ff                   	(bad)  
    5add:	ff                   	(bad)  
    5ade:	ff                   	(bad)  
    5adf:	ff                   	(bad)  
    5ae0:	ff                   	(bad)  
    5ae1:	ff                   	(bad)  
    5ae2:	ff                   	(bad)  
    5ae3:	ff                   	(bad)  
    5ae4:	ff                   	(bad)  
    5ae5:	ff                   	(bad)  
    5ae6:	ff                   	(bad)  
    5ae7:	ff                   	(bad)  
    5ae8:	ff                   	(bad)  
    5ae9:	ff                   	(bad)  
    5aea:	ff                   	(bad)  
    5aeb:	ff                   	(bad)  
    5aec:	ff                   	(bad)  
    5aed:	ff                   	(bad)  
    5aee:	ff                   	(bad)  
    5aef:	ff                   	(bad)  
    5af0:	ff                   	(bad)  
    5af1:	ff                   	(bad)  
    5af2:	ff                   	(bad)  
    5af3:	ff                   	(bad)  
    5af4:	ff                   	(bad)  
    5af5:	ff                   	(bad)  
    5af6:	ff                   	(bad)  
    5af7:	ff                   	(bad)  
    5af8:	ff                   	(bad)  
    5af9:	ff                   	(bad)  
    5afa:	ff                   	(bad)  
    5afb:	ff                   	(bad)  
    5afc:	ff                   	(bad)  
    5afd:	ff                   	(bad)  
    5afe:	ff                   	(bad)  
    5aff:	ff                   	(bad)  
    5b00:	ff                   	(bad)  
    5b01:	ff                   	(bad)  
    5b02:	ff                   	(bad)  
    5b03:	ff                   	(bad)  
    5b04:	ff                   	(bad)  
    5b05:	ff                   	(bad)  
    5b06:	ff                   	(bad)  
    5b07:	ff                   	(bad)  
    5b08:	ff                   	(bad)  
    5b09:	ff                   	(bad)  
    5b0a:	ff                   	(bad)  
    5b0b:	ff                   	(bad)  
    5b0c:	ff                   	(bad)  
    5b0d:	ff                   	(bad)  
    5b0e:	ff                   	(bad)  
    5b0f:	ff                   	(bad)  
    5b10:	ff                   	(bad)  
    5b11:	ff                   	(bad)  
    5b12:	ff                   	(bad)  
    5b13:	ff                   	(bad)  
    5b14:	ff                   	(bad)  
    5b15:	ff                   	(bad)  
    5b16:	ff                   	(bad)  
    5b17:	ff                   	(bad)  
    5b18:	ff                   	(bad)  
    5b19:	ff                   	(bad)  
    5b1a:	ff                   	(bad)  
    5b1b:	ff                   	(bad)  
    5b1c:	ff                   	(bad)  
    5b1d:	ff                   	(bad)  
    5b1e:	ff                   	(bad)  
    5b1f:	ff                   	(bad)  
    5b20:	ff                   	(bad)  
    5b21:	ff                   	(bad)  
    5b22:	ff                   	(bad)  
    5b23:	ff                   	(bad)  
    5b24:	ff                   	(bad)  
    5b25:	ff                   	(bad)  
    5b26:	ff                   	(bad)  
    5b27:	ff                   	(bad)  
    5b28:	ff                   	(bad)  
    5b29:	ff                   	(bad)  
    5b2a:	ff                   	(bad)  
    5b2b:	ff                   	(bad)  
    5b2c:	ff                   	(bad)  
    5b2d:	ff                   	(bad)  
    5b2e:	ff                   	(bad)  
    5b2f:	ff                   	(bad)  
    5b30:	ff                   	(bad)  
    5b31:	ff                   	(bad)  
    5b32:	ff                   	(bad)  
    5b33:	ff                   	(bad)  
    5b34:	ff                   	(bad)  
    5b35:	ff                   	(bad)  
    5b36:	ff                   	(bad)  
    5b37:	ff                   	(bad)  
    5b38:	ff                   	(bad)  
    5b39:	ff                   	(bad)  
    5b3a:	ff                   	(bad)  
    5b3b:	ff                   	(bad)  
    5b3c:	ff                   	(bad)  
    5b3d:	ff                   	(bad)  
    5b3e:	ff                   	(bad)  
    5b3f:	ff                   	(bad)  
    5b40:	ff                   	(bad)  
    5b41:	ff                   	(bad)  
    5b42:	ff                   	(bad)  
    5b43:	ff                   	(bad)  
    5b44:	ff                   	(bad)  
    5b45:	ff                   	(bad)  
    5b46:	ff                   	(bad)  
    5b47:	ff                   	(bad)  
    5b48:	ff                   	(bad)  
    5b49:	ff                   	(bad)  
    5b4a:	ff                   	(bad)  
    5b4b:	ff                   	(bad)  
    5b4c:	ff                   	(bad)  
    5b4d:	ff                   	(bad)  
    5b4e:	ff                   	(bad)  
    5b4f:	ff                   	(bad)  
    5b50:	ff                   	(bad)  
    5b51:	ff                   	(bad)  
    5b52:	ff                   	(bad)  
    5b53:	ff                   	(bad)  
    5b54:	ff                   	(bad)  
    5b55:	ff                   	(bad)  
    5b56:	ff                   	(bad)  
    5b57:	ff                   	(bad)  
    5b58:	ff                   	(bad)  
    5b59:	ff                   	(bad)  
    5b5a:	ff                   	(bad)  
    5b5b:	ff                   	(bad)  
    5b5c:	ff                   	(bad)  
    5b5d:	ff                   	(bad)  
    5b5e:	ff                   	(bad)  
    5b5f:	ff                   	(bad)  
    5b60:	ff                   	(bad)  
    5b61:	ff                   	(bad)  
    5b62:	ff                   	(bad)  
    5b63:	ff                   	(bad)  
    5b64:	ff                   	(bad)  
    5b65:	ff                   	(bad)  
    5b66:	ff                   	(bad)  
    5b67:	ff                   	(bad)  
    5b68:	ff                   	(bad)  
    5b69:	ff                   	(bad)  
    5b6a:	ff                   	(bad)  
    5b6b:	ff                   	(bad)  
    5b6c:	ff                   	(bad)  
    5b6d:	ff                   	(bad)  
    5b6e:	ff                   	(bad)  
    5b6f:	ff                   	(bad)  
    5b70:	ff                   	(bad)  
    5b71:	ff                   	(bad)  
    5b72:	ff                   	(bad)  
    5b73:	ff                   	(bad)  
    5b74:	ff                   	(bad)  
    5b75:	ff                   	(bad)  
    5b76:	ff                   	(bad)  
    5b77:	ff                   	(bad)  
    5b78:	ff                   	(bad)  
    5b79:	ff                   	(bad)  
    5b7a:	ff                   	(bad)  
    5b7b:	ff                   	(bad)  
    5b7c:	ff                   	(bad)  
    5b7d:	ff                   	(bad)  
    5b7e:	ff                   	(bad)  
    5b7f:	ff                   	(bad)  
    5b80:	ff                   	(bad)  
    5b81:	ff                   	(bad)  
    5b82:	ff                   	(bad)  
    5b83:	ff                   	(bad)  
    5b84:	ff                   	(bad)  
    5b85:	ff                   	(bad)  
    5b86:	ff                   	(bad)  
    5b87:	ff                   	(bad)  
    5b88:	ff                   	(bad)  
    5b89:	ff                   	(bad)  
    5b8a:	ff                   	(bad)  
    5b8b:	ff                   	(bad)  
    5b8c:	ff                   	(bad)  
    5b8d:	ff                   	(bad)  
    5b8e:	ff                   	(bad)  
    5b8f:	ff                   	(bad)  
    5b90:	ff                   	(bad)  
    5b91:	ff                   	(bad)  
    5b92:	ff                   	(bad)  
    5b93:	ff                   	(bad)  
    5b94:	ff                   	(bad)  
    5b95:	ff                   	(bad)  
    5b96:	ff                   	(bad)  
    5b97:	ff                   	(bad)  
    5b98:	ff                   	(bad)  
    5b99:	ff                   	(bad)  
    5b9a:	ff                   	(bad)  
    5b9b:	ff                   	(bad)  
    5b9c:	ff                   	(bad)  
    5b9d:	ff                   	(bad)  
    5b9e:	ff                   	(bad)  
    5b9f:	ff                   	(bad)  
    5ba0:	ff                   	(bad)  
    5ba1:	ff                   	(bad)  
    5ba2:	ff                   	(bad)  
    5ba3:	ff                   	(bad)  
    5ba4:	ff                   	(bad)  
    5ba5:	ff                   	(bad)  
    5ba6:	ff                   	(bad)  
    5ba7:	ff                   	(bad)  
    5ba8:	ff                   	(bad)  
    5ba9:	ff                   	(bad)  
    5baa:	ff                   	(bad)  
    5bab:	ff                   	(bad)  
    5bac:	ff                   	(bad)  
    5bad:	ff                   	(bad)  
    5bae:	ff                   	(bad)  
    5baf:	ff                   	(bad)  
    5bb0:	ff                   	(bad)  
    5bb1:	ff                   	(bad)  
    5bb2:	ff                   	(bad)  
    5bb3:	ff                   	(bad)  
    5bb4:	ff                   	(bad)  
    5bb5:	ff                   	(bad)  
    5bb6:	ff                   	(bad)  
    5bb7:	ff                   	(bad)  
    5bb8:	ff                   	(bad)  
    5bb9:	ff                   	(bad)  
    5bba:	ff                   	(bad)  
    5bbb:	ff                   	(bad)  
    5bbc:	ff                   	(bad)  
    5bbd:	ff                   	(bad)  
    5bbe:	ff                   	(bad)  
    5bbf:	ff                   	(bad)  
    5bc0:	ff                   	(bad)  
    5bc1:	ff                   	(bad)  
    5bc2:	ff                   	(bad)  
    5bc3:	ff                   	(bad)  
    5bc4:	ff                   	(bad)  
    5bc5:	ff                   	(bad)  
    5bc6:	ff                   	(bad)  
    5bc7:	ff                   	(bad)  
    5bc8:	ff                   	(bad)  
    5bc9:	ff                   	(bad)  
    5bca:	ff                   	(bad)  
    5bcb:	ff                   	(bad)  
    5bcc:	ff                   	(bad)  
    5bcd:	ff                   	(bad)  
    5bce:	ff                   	(bad)  
    5bcf:	ff                   	(bad)  
    5bd0:	ff                   	(bad)  
    5bd1:	ff                   	(bad)  
    5bd2:	ff                   	(bad)  
    5bd3:	ff                   	(bad)  
    5bd4:	ff                   	(bad)  
    5bd5:	ff                   	(bad)  
    5bd6:	ff                   	(bad)  
    5bd7:	ff                   	(bad)  
    5bd8:	ff                   	(bad)  
    5bd9:	ff                   	(bad)  
    5bda:	ff                   	(bad)  
    5bdb:	ff                   	(bad)  
    5bdc:	ff                   	(bad)  
    5bdd:	ff                   	(bad)  
    5bde:	ff                   	(bad)  
    5bdf:	ff                   	(bad)  
    5be0:	ff                   	(bad)  
    5be1:	ff                   	(bad)  
    5be2:	ff                   	(bad)  
    5be3:	ff                   	(bad)  
    5be4:	ff                   	(bad)  
    5be5:	ff                   	(bad)  
    5be6:	ff                   	(bad)  
    5be7:	ff                   	(bad)  
    5be8:	ff                   	(bad)  
    5be9:	ff                   	(bad)  
    5bea:	ff                   	(bad)  
    5beb:	ff                   	(bad)  
    5bec:	ff                   	(bad)  
    5bed:	ff                   	(bad)  
    5bee:	ff                   	(bad)  
    5bef:	ff                   	(bad)  
    5bf0:	ff                   	(bad)  
    5bf1:	ff                   	(bad)  
    5bf2:	ff                   	(bad)  
    5bf3:	ff                   	(bad)  
    5bf4:	ff                   	(bad)  
    5bf5:	ff                   	(bad)  
    5bf6:	ff                   	(bad)  
    5bf7:	ff                   	(bad)  
    5bf8:	ff                   	(bad)  
    5bf9:	ff                   	(bad)  
    5bfa:	ff                   	(bad)  
    5bfb:	ff                   	(bad)  
    5bfc:	ff                   	(bad)  
    5bfd:	ff                   	(bad)  
    5bfe:	ff                   	(bad)  
    5bff:	ff                   	(bad)  
    5c00:	ff                   	(bad)  
    5c01:	ff                   	(bad)  
    5c02:	ff                   	(bad)  
    5c03:	ff                   	(bad)  
    5c04:	ff                   	(bad)  
    5c05:	ff                   	(bad)  
    5c06:	ff                   	(bad)  
    5c07:	ff                   	(bad)  
    5c08:	ff                   	(bad)  
    5c09:	ff                   	(bad)  
    5c0a:	ff                   	(bad)  
    5c0b:	ff                   	(bad)  
    5c0c:	ff                   	(bad)  
    5c0d:	ff                   	(bad)  
    5c0e:	ff                   	(bad)  
    5c0f:	ff                   	(bad)  
    5c10:	ff                   	(bad)  
    5c11:	ff                   	(bad)  
    5c12:	ff                   	(bad)  
    5c13:	ff                   	(bad)  
    5c14:	ff                   	(bad)  
    5c15:	ff                   	(bad)  
    5c16:	ff                   	(bad)  
    5c17:	ff                   	(bad)  
    5c18:	ff                   	(bad)  
    5c19:	ff                   	(bad)  
    5c1a:	ff                   	(bad)  
    5c1b:	ff                   	(bad)  
    5c1c:	ff                   	(bad)  
    5c1d:	ff                   	(bad)  
    5c1e:	ff                   	(bad)  
    5c1f:	ff                   	(bad)  
    5c20:	ff                   	(bad)  
    5c21:	ff                   	(bad)  
    5c22:	ff                   	(bad)  
    5c23:	ff                   	(bad)  
    5c24:	ff                   	(bad)  
    5c25:	ff                   	(bad)  
    5c26:	ff                   	(bad)  
    5c27:	ff                   	(bad)  
    5c28:	ff                   	(bad)  
    5c29:	ff                   	(bad)  
    5c2a:	ff                   	(bad)  
    5c2b:	ff                   	(bad)  
    5c2c:	ff                   	(bad)  
    5c2d:	ff                   	(bad)  
    5c2e:	ff                   	(bad)  
    5c2f:	ff                   	(bad)  
    5c30:	ff                   	(bad)  
    5c31:	ff                   	(bad)  
    5c32:	ff                   	(bad)  
    5c33:	ff                   	(bad)  
    5c34:	ff                   	(bad)  
    5c35:	ff                   	(bad)  
    5c36:	ff                   	(bad)  
    5c37:	ff                   	(bad)  
    5c38:	ff                   	(bad)  
    5c39:	ff                   	(bad)  
    5c3a:	ff                   	(bad)  
    5c3b:	ff                   	(bad)  
    5c3c:	ff                   	(bad)  
    5c3d:	ff                   	(bad)  
    5c3e:	ff                   	(bad)  
    5c3f:	ff                   	(bad)  
    5c40:	ff                   	(bad)  
    5c41:	ff                   	(bad)  
    5c42:	ff                   	(bad)  
    5c43:	ff                   	(bad)  
    5c44:	ff                   	(bad)  
    5c45:	ff                   	(bad)  
    5c46:	ff                   	(bad)  
    5c47:	ff                   	(bad)  
    5c48:	ff                   	(bad)  
    5c49:	ff                   	(bad)  
    5c4a:	ff                   	(bad)  
    5c4b:	ff                   	(bad)  
    5c4c:	ff                   	(bad)  
    5c4d:	ff                   	(bad)  
    5c4e:	ff                   	(bad)  
    5c4f:	ff                   	(bad)  
    5c50:	ff                   	(bad)  
    5c51:	ff                   	(bad)  
    5c52:	ff                   	(bad)  
    5c53:	ff                   	(bad)  
    5c54:	ff                   	(bad)  
    5c55:	ff                   	(bad)  
    5c56:	ff                   	(bad)  
    5c57:	ff                   	(bad)  
    5c58:	ff                   	(bad)  
    5c59:	ff                   	(bad)  
    5c5a:	ff                   	(bad)  
    5c5b:	ff                   	(bad)  
    5c5c:	ff                   	(bad)  
    5c5d:	ff                   	(bad)  
    5c5e:	ff                   	(bad)  
    5c5f:	ff                   	(bad)  
    5c60:	ff                   	(bad)  
    5c61:	ff                   	(bad)  
    5c62:	ff                   	(bad)  
    5c63:	ff                   	(bad)  
    5c64:	ff                   	(bad)  
    5c65:	ff                   	(bad)  
    5c66:	ff                   	(bad)  
    5c67:	ff                   	(bad)  
    5c68:	ff                   	(bad)  
    5c69:	ff                   	(bad)  
    5c6a:	ff                   	(bad)  
    5c6b:	ff                   	(bad)  
    5c6c:	ff                   	(bad)  
    5c6d:	ff                   	(bad)  
    5c6e:	ff                   	(bad)  
    5c6f:	ff                   	(bad)  
    5c70:	ff                   	(bad)  
    5c71:	ff                   	(bad)  
    5c72:	ff                   	(bad)  
    5c73:	ff                   	(bad)  
    5c74:	ff                   	(bad)  
    5c75:	ff                   	(bad)  
    5c76:	ff                   	(bad)  
    5c77:	ff                   	(bad)  
    5c78:	ff                   	(bad)  
    5c79:	ff                   	(bad)  
    5c7a:	ff                   	(bad)  
    5c7b:	ff                   	(bad)  
    5c7c:	ff                   	(bad)  
    5c7d:	ff                   	(bad)  
    5c7e:	ff                   	(bad)  
    5c7f:	ff                   	(bad)  
    5c80:	ff                   	(bad)  
    5c81:	ff                   	(bad)  
    5c82:	ff                   	(bad)  
    5c83:	ff                   	(bad)  
    5c84:	ff                   	(bad)  
    5c85:	ff                   	(bad)  
    5c86:	ff                   	(bad)  
    5c87:	ff                   	(bad)  
    5c88:	ff                   	(bad)  
    5c89:	ff                   	(bad)  
    5c8a:	ff                   	(bad)  
    5c8b:	ff                   	(bad)  
    5c8c:	ff                   	(bad)  
    5c8d:	ff                   	(bad)  
    5c8e:	ff                   	(bad)  
    5c8f:	ff                   	(bad)  
    5c90:	ff                   	(bad)  
    5c91:	ff                   	(bad)  
    5c92:	ff                   	(bad)  
    5c93:	ff                   	(bad)  
    5c94:	ff                   	(bad)  
    5c95:	ff                   	(bad)  
    5c96:	ff                   	(bad)  
    5c97:	ff                   	(bad)  
    5c98:	ff                   	(bad)  
    5c99:	ff                   	(bad)  
    5c9a:	ff                   	(bad)  
    5c9b:	ff                   	(bad)  
    5c9c:	ff                   	(bad)  
    5c9d:	ff                   	(bad)  
    5c9e:	ff                   	(bad)  
    5c9f:	ff                   	(bad)  
    5ca0:	ff                   	(bad)  
    5ca1:	ff                   	(bad)  
    5ca2:	ff                   	(bad)  
    5ca3:	ff                   	(bad)  
    5ca4:	ff                   	(bad)  
    5ca5:	ff                   	(bad)  
    5ca6:	ff                   	(bad)  
    5ca7:	ff                   	(bad)  
    5ca8:	ff                   	(bad)  
    5ca9:	ff                   	(bad)  
    5caa:	ff                   	(bad)  
    5cab:	ff                   	(bad)  
    5cac:	ff                   	(bad)  
    5cad:	ff                   	(bad)  
    5cae:	ff                   	(bad)  
    5caf:	ff                   	(bad)  
    5cb0:	ff                   	(bad)  
    5cb1:	ff                   	(bad)  
    5cb2:	ff                   	(bad)  
    5cb3:	ff                   	(bad)  
    5cb4:	ff                   	(bad)  
    5cb5:	ff                   	(bad)  
    5cb6:	ff                   	(bad)  
    5cb7:	ff                   	(bad)  
    5cb8:	ff                   	(bad)  
    5cb9:	ff                   	(bad)  
    5cba:	ff                   	(bad)  
    5cbb:	ff                   	(bad)  
    5cbc:	ff                   	(bad)  
    5cbd:	ff                   	(bad)  
    5cbe:	ff                   	(bad)  
    5cbf:	ff                   	(bad)  
    5cc0:	ff                   	(bad)  
    5cc1:	ff                   	(bad)  
    5cc2:	ff                   	(bad)  
    5cc3:	ff                   	(bad)  
    5cc4:	ff                   	(bad)  
    5cc5:	ff                   	(bad)  
    5cc6:	ff                   	(bad)  
    5cc7:	ff                   	(bad)  
    5cc8:	ff                   	(bad)  
    5cc9:	ff                   	(bad)  
    5cca:	ff                   	(bad)  
    5ccb:	ff                   	(bad)  
    5ccc:	ff                   	(bad)  
    5ccd:	ff                   	(bad)  
    5cce:	ff                   	(bad)  
    5ccf:	ff                   	(bad)  
    5cd0:	ff                   	(bad)  
    5cd1:	ff                   	(bad)  
    5cd2:	ff                   	(bad)  
    5cd3:	ff                   	(bad)  
    5cd4:	ff                   	(bad)  
    5cd5:	ff                   	(bad)  
    5cd6:	ff                   	(bad)  
    5cd7:	ff                   	(bad)  
    5cd8:	ff                   	(bad)  
    5cd9:	ff                   	(bad)  
    5cda:	ff                   	(bad)  
    5cdb:	ff                   	(bad)  
    5cdc:	ff                   	(bad)  
    5cdd:	ff                   	(bad)  
    5cde:	ff                   	(bad)  
    5cdf:	ff                   	(bad)  
    5ce0:	ff                   	(bad)  
    5ce1:	ff                   	(bad)  
    5ce2:	ff                   	(bad)  
    5ce3:	ff                   	(bad)  
    5ce4:	ff                   	(bad)  
    5ce5:	ff                   	(bad)  
    5ce6:	ff                   	(bad)  
    5ce7:	ff                   	(bad)  
    5ce8:	ff                   	(bad)  
    5ce9:	ff                   	(bad)  
    5cea:	ff                   	(bad)  
    5ceb:	ff                   	(bad)  
    5cec:	ff                   	(bad)  
    5ced:	ff                   	(bad)  
    5cee:	ff                   	(bad)  
    5cef:	ff                   	(bad)  
    5cf0:	ff                   	(bad)  
    5cf1:	ff                   	(bad)  
    5cf2:	ff                   	(bad)  
    5cf3:	ff                   	(bad)  
    5cf4:	ff                   	(bad)  
    5cf5:	ff                   	(bad)  
    5cf6:	ff                   	(bad)  
    5cf7:	ff                   	(bad)  
    5cf8:	ff                   	(bad)  
    5cf9:	ff                   	(bad)  
    5cfa:	ff                   	(bad)  
    5cfb:	ff                   	(bad)  
    5cfc:	ff                   	(bad)  
    5cfd:	ff                   	(bad)  
    5cfe:	ff                   	(bad)  
    5cff:	ff                   	(bad)  
    5d00:	ff                   	(bad)  
    5d01:	ff                   	(bad)  
    5d02:	ff                   	(bad)  
    5d03:	ff                   	(bad)  
    5d04:	ff                   	(bad)  
    5d05:	ff                   	(bad)  
    5d06:	ff                   	(bad)  
    5d07:	ff                   	(bad)  
    5d08:	ff                   	(bad)  
    5d09:	ff                   	(bad)  
    5d0a:	ff                   	(bad)  
    5d0b:	ff                   	(bad)  
    5d0c:	ff                   	(bad)  
    5d0d:	ff                   	(bad)  
    5d0e:	ff                   	(bad)  
    5d0f:	ff                   	(bad)  
    5d10:	ff                   	(bad)  
    5d11:	ff                   	(bad)  
    5d12:	ff                   	(bad)  
    5d13:	ff                   	(bad)  
    5d14:	ff                   	(bad)  
    5d15:	ff                   	(bad)  
    5d16:	ff                   	(bad)  
    5d17:	ff                   	(bad)  
    5d18:	ff                   	(bad)  
    5d19:	ff                   	(bad)  
    5d1a:	ff                   	(bad)  
    5d1b:	ff                   	(bad)  
    5d1c:	ff                   	(bad)  
    5d1d:	ff                   	(bad)  
    5d1e:	ff                   	(bad)  
    5d1f:	ff                   	(bad)  
    5d20:	ff                   	(bad)  
    5d21:	ff                   	(bad)  
    5d22:	ff                   	(bad)  
    5d23:	ff                   	(bad)  
    5d24:	ff                   	(bad)  
    5d25:	ff                   	(bad)  
    5d26:	ff                   	(bad)  
    5d27:	ff                   	(bad)  
    5d28:	ff                   	(bad)  
    5d29:	ff                   	(bad)  
    5d2a:	ff                   	(bad)  
    5d2b:	ff                   	(bad)  
    5d2c:	ff                   	(bad)  
    5d2d:	ff                   	(bad)  
    5d2e:	ff                   	(bad)  
    5d2f:	ff                   	(bad)  
    5d30:	ff                   	(bad)  
    5d31:	ff                   	(bad)  
    5d32:	ff                   	(bad)  
    5d33:	ff                   	(bad)  
    5d34:	ff                   	(bad)  
    5d35:	ff                   	(bad)  
    5d36:	ff                   	(bad)  
    5d37:	ff                   	(bad)  
    5d38:	ff                   	(bad)  
    5d39:	ff                   	(bad)  
    5d3a:	ff                   	(bad)  
    5d3b:	ff                   	(bad)  
    5d3c:	ff                   	(bad)  
    5d3d:	ff                   	(bad)  
    5d3e:	ff                   	(bad)  
    5d3f:	ff                   	(bad)  
    5d40:	ff                   	(bad)  
    5d41:	ff                   	(bad)  
    5d42:	ff                   	(bad)  
    5d43:	ff                   	(bad)  
    5d44:	ff                   	(bad)  
    5d45:	ff                   	(bad)  
    5d46:	ff                   	(bad)  
    5d47:	ff                   	(bad)  
    5d48:	ff                   	(bad)  
    5d49:	ff                   	(bad)  
    5d4a:	ff                   	(bad)  
    5d4b:	ff                   	(bad)  
    5d4c:	ff                   	(bad)  
    5d4d:	ff                   	(bad)  
    5d4e:	ff                   	(bad)  
    5d4f:	ff                   	(bad)  
    5d50:	ff                   	(bad)  
    5d51:	ff                   	(bad)  
    5d52:	ff                   	(bad)  
    5d53:	ff                   	(bad)  
    5d54:	ff                   	(bad)  
    5d55:	ff                   	(bad)  
    5d56:	ff                   	(bad)  
    5d57:	ff                   	(bad)  
    5d58:	ff                   	(bad)  
    5d59:	ff                   	(bad)  
    5d5a:	ff                   	(bad)  
    5d5b:	ff                   	(bad)  
    5d5c:	ff                   	(bad)  
    5d5d:	ff                   	(bad)  
    5d5e:	ff                   	(bad)  
    5d5f:	ff                   	(bad)  
    5d60:	ff                   	(bad)  
    5d61:	ff                   	(bad)  
    5d62:	ff                   	(bad)  
    5d63:	ff                   	(bad)  
    5d64:	ff                   	(bad)  
    5d65:	ff                   	(bad)  
    5d66:	ff                   	(bad)  
    5d67:	ff                   	(bad)  
    5d68:	ff                   	(bad)  
    5d69:	ff                   	(bad)  
    5d6a:	ff                   	(bad)  
    5d6b:	ff                   	(bad)  
    5d6c:	ff                   	(bad)  
    5d6d:	ff                   	(bad)  
    5d6e:	ff                   	(bad)  
    5d6f:	ff                   	(bad)  
    5d70:	ff                   	(bad)  
    5d71:	ff                   	(bad)  
    5d72:	ff                   	(bad)  
    5d73:	ff                   	(bad)  
    5d74:	ff                   	(bad)  
    5d75:	ff                   	(bad)  
    5d76:	ff                   	(bad)  
    5d77:	ff                   	(bad)  
    5d78:	ff                   	(bad)  
    5d79:	ff                   	(bad)  
    5d7a:	ff                   	(bad)  
    5d7b:	ff                   	(bad)  
    5d7c:	ff                   	(bad)  
    5d7d:	ff                   	(bad)  
    5d7e:	ff                   	(bad)  
    5d7f:	ff                   	(bad)  
    5d80:	ff                   	(bad)  
    5d81:	ff                   	(bad)  
    5d82:	ff                   	(bad)  
    5d83:	ff                   	(bad)  
    5d84:	ff                   	(bad)  
    5d85:	ff                   	(bad)  
    5d86:	ff                   	(bad)  
    5d87:	ff                   	(bad)  
    5d88:	ff                   	(bad)  
    5d89:	ff                   	(bad)  
    5d8a:	ff                   	(bad)  
    5d8b:	ff                   	(bad)  
    5d8c:	ff                   	(bad)  
    5d8d:	ff                   	(bad)  
    5d8e:	ff                   	(bad)  
    5d8f:	ff                   	(bad)  
    5d90:	ff                   	(bad)  
    5d91:	ff                   	(bad)  
    5d92:	ff                   	(bad)  
    5d93:	ff                   	(bad)  
    5d94:	ff                   	(bad)  
    5d95:	ff                   	(bad)  
    5d96:	ff                   	(bad)  
    5d97:	ff                   	(bad)  
    5d98:	ff                   	(bad)  
    5d99:	ff                   	(bad)  
    5d9a:	ff                   	(bad)  
    5d9b:	ff                   	(bad)  
    5d9c:	ff                   	(bad)  
    5d9d:	ff                   	(bad)  
    5d9e:	ff                   	(bad)  
    5d9f:	ff                   	(bad)  
    5da0:	ff                   	(bad)  
    5da1:	ff                   	(bad)  
    5da2:	ff                   	(bad)  
    5da3:	ff                   	(bad)  
    5da4:	ff                   	(bad)  
    5da5:	ff                   	(bad)  
    5da6:	ff                   	(bad)  
    5da7:	ff                   	(bad)  
    5da8:	ff                   	(bad)  
    5da9:	ff                   	(bad)  
    5daa:	ff                   	(bad)  
    5dab:	ff                   	(bad)  
    5dac:	ff                   	(bad)  
    5dad:	ff                   	(bad)  
    5dae:	ff                   	(bad)  
    5daf:	ff                   	(bad)  
    5db0:	ff                   	(bad)  
    5db1:	ff                   	(bad)  
    5db2:	ff                   	(bad)  
    5db3:	ff                   	(bad)  
    5db4:	ff                   	(bad)  
    5db5:	ff                   	(bad)  
    5db6:	ff                   	(bad)  
    5db7:	ff                   	(bad)  
    5db8:	ff                   	(bad)  
    5db9:	ff                   	(bad)  
    5dba:	ff                   	(bad)  
    5dbb:	ff                   	(bad)  
    5dbc:	ff                   	(bad)  
    5dbd:	ff                   	(bad)  
    5dbe:	ff                   	(bad)  
    5dbf:	ff                   	(bad)  
    5dc0:	ff                   	(bad)  
    5dc1:	ff                   	(bad)  
    5dc2:	ff                   	(bad)  
    5dc3:	ff                   	(bad)  
    5dc4:	ff                   	(bad)  
    5dc5:	ff                   	(bad)  
    5dc6:	ff                   	(bad)  
    5dc7:	ff                   	(bad)  
    5dc8:	ff                   	(bad)  
    5dc9:	ff                   	(bad)  
    5dca:	ff                   	(bad)  
    5dcb:	ff                   	(bad)  
    5dcc:	ff                   	(bad)  
    5dcd:	ff                   	(bad)  
    5dce:	ff                   	(bad)  
    5dcf:	ff                   	(bad)  
    5dd0:	ff                   	(bad)  
    5dd1:	ff                   	(bad)  
    5dd2:	ff                   	(bad)  
    5dd3:	ff                   	(bad)  
    5dd4:	ff                   	(bad)  
    5dd5:	ff                   	(bad)  
    5dd6:	ff                   	(bad)  
    5dd7:	ff                   	(bad)  
    5dd8:	ff                   	(bad)  
    5dd9:	ff                   	(bad)  
    5dda:	ff                   	(bad)  
    5ddb:	ff                   	(bad)  
    5ddc:	ff                   	(bad)  
    5ddd:	ff                   	(bad)  
    5dde:	ff                   	(bad)  
    5ddf:	ff                   	(bad)  
    5de0:	ff                   	(bad)  
    5de1:	ff                   	(bad)  
    5de2:	ff                   	(bad)  
    5de3:	ff                   	(bad)  
    5de4:	ff                   	(bad)  
    5de5:	ff                   	(bad)  
    5de6:	ff                   	(bad)  
    5de7:	ff                   	(bad)  
    5de8:	ff                   	(bad)  
    5de9:	ff                   	(bad)  
    5dea:	ff                   	(bad)  
    5deb:	ff                   	(bad)  
    5dec:	ff                   	(bad)  
    5ded:	ff                   	(bad)  
    5dee:	ff                   	(bad)  
    5def:	ff                   	(bad)  
    5df0:	ff                   	(bad)  
    5df1:	ff                   	(bad)  
    5df2:	ff                   	(bad)  
    5df3:	ff                   	(bad)  
    5df4:	ff                   	(bad)  
    5df5:	ff                   	(bad)  
    5df6:	ff                   	(bad)  
    5df7:	ff                   	(bad)  
    5df8:	ff                   	(bad)  
    5df9:	ff                   	(bad)  
    5dfa:	ff                   	(bad)  
    5dfb:	ff                   	(bad)  
    5dfc:	ff                   	(bad)  
    5dfd:	ff                   	(bad)  
    5dfe:	ff                   	(bad)  
    5dff:	ff                   	(bad)  
    5e00:	ff                   	(bad)  
    5e01:	ff                   	(bad)  
    5e02:	ff                   	(bad)  
    5e03:	ff                   	(bad)  
    5e04:	ff                   	(bad)  
    5e05:	ff                   	(bad)  
    5e06:	ff                   	(bad)  
    5e07:	ff                   	(bad)  
    5e08:	ff                   	(bad)  
    5e09:	ff                   	(bad)  
    5e0a:	ff                   	(bad)  
    5e0b:	ff                   	(bad)  
    5e0c:	ff                   	(bad)  
    5e0d:	ff                   	(bad)  
    5e0e:	ff                   	(bad)  
    5e0f:	ff                   	(bad)  
    5e10:	ff                   	(bad)  
    5e11:	ff                   	(bad)  
    5e12:	ff                   	(bad)  
    5e13:	ff                   	(bad)  
    5e14:	ff                   	(bad)  
    5e15:	ff                   	(bad)  
    5e16:	ff                   	(bad)  
    5e17:	ff                   	(bad)  
    5e18:	ff                   	(bad)  
    5e19:	ff                   	(bad)  
    5e1a:	ff                   	(bad)  
    5e1b:	ff                   	(bad)  
    5e1c:	ff                   	(bad)  
    5e1d:	ff                   	(bad)  
    5e1e:	ff                   	(bad)  
    5e1f:	ff                   	(bad)  
    5e20:	ff                   	(bad)  
    5e21:	ff                   	(bad)  
    5e22:	ff                   	(bad)  
    5e23:	ff                   	(bad)  
    5e24:	ff                   	(bad)  
    5e25:	ff                   	(bad)  
    5e26:	ff                   	(bad)  
    5e27:	ff                   	(bad)  
    5e28:	ff                   	(bad)  
    5e29:	ff                   	(bad)  
    5e2a:	ff                   	(bad)  
    5e2b:	ff                   	(bad)  
    5e2c:	ff                   	(bad)  
    5e2d:	ff                   	(bad)  
    5e2e:	ff                   	(bad)  
    5e2f:	ff                   	(bad)  
    5e30:	ff                   	(bad)  
    5e31:	ff                   	(bad)  
    5e32:	ff                   	(bad)  
    5e33:	ff                   	(bad)  
    5e34:	ff                   	(bad)  
    5e35:	ff                   	(bad)  
    5e36:	ff                   	(bad)  
    5e37:	ff                   	(bad)  
    5e38:	ff                   	(bad)  
    5e39:	ff                   	(bad)  
    5e3a:	ff                   	(bad)  
    5e3b:	ff                   	(bad)  
    5e3c:	ff                   	(bad)  
    5e3d:	ff                   	(bad)  
    5e3e:	ff                   	(bad)  
    5e3f:	ff                   	(bad)  
    5e40:	ff                   	(bad)  
    5e41:	ff                   	(bad)  
    5e42:	ff                   	(bad)  
    5e43:	ff                   	(bad)  
    5e44:	ff                   	(bad)  
    5e45:	ff                   	(bad)  
    5e46:	ff                   	(bad)  
    5e47:	ff                   	(bad)  
    5e48:	ff                   	(bad)  
    5e49:	ff                   	(bad)  
    5e4a:	ff                   	(bad)  
    5e4b:	ff                   	(bad)  
    5e4c:	ff                   	(bad)  
    5e4d:	ff                   	(bad)  
    5e4e:	ff                   	(bad)  
    5e4f:	ff                   	(bad)  
    5e50:	ff                   	(bad)  
    5e51:	ff                   	(bad)  
    5e52:	ff                   	(bad)  
    5e53:	ff                   	(bad)  
    5e54:	ff                   	(bad)  
    5e55:	ff                   	(bad)  
    5e56:	ff                   	(bad)  
    5e57:	ff                   	(bad)  
    5e58:	ff                   	(bad)  
    5e59:	ff                   	(bad)  
    5e5a:	ff                   	(bad)  
    5e5b:	ff                   	(bad)  
    5e5c:	ff                   	(bad)  
    5e5d:	ff                   	(bad)  
    5e5e:	ff                   	(bad)  
    5e5f:	ff                   	(bad)  
    5e60:	ff                   	(bad)  
    5e61:	ff                   	(bad)  
    5e62:	ff                   	(bad)  
    5e63:	ff                   	(bad)  
    5e64:	ff                   	(bad)  
    5e65:	ff                   	(bad)  
    5e66:	ff                   	(bad)  
    5e67:	ff                   	(bad)  
    5e68:	ff                   	(bad)  
    5e69:	ff                   	(bad)  
    5e6a:	ff                   	(bad)  
    5e6b:	ff                   	(bad)  
    5e6c:	ff                   	(bad)  
    5e6d:	ff                   	(bad)  
    5e6e:	ff                   	(bad)  
    5e6f:	ff                   	(bad)  
    5e70:	ff                   	(bad)  
    5e71:	ff                   	(bad)  
    5e72:	ff                   	(bad)  
    5e73:	ff                   	(bad)  
    5e74:	ff                   	(bad)  
    5e75:	ff                   	(bad)  
    5e76:	ff                   	(bad)  
    5e77:	ff                   	(bad)  
    5e78:	ff                   	(bad)  
    5e79:	ff                   	(bad)  
    5e7a:	ff                   	(bad)  
    5e7b:	ff                   	(bad)  
    5e7c:	ff                   	(bad)  
    5e7d:	ff                   	(bad)  
    5e7e:	ff                   	(bad)  
    5e7f:	ff                   	(bad)  
    5e80:	ff                   	(bad)  
    5e81:	ff                   	(bad)  
    5e82:	ff                   	(bad)  
    5e83:	ff                   	(bad)  
    5e84:	ff                   	(bad)  
    5e85:	ff                   	(bad)  
    5e86:	ff                   	(bad)  
    5e87:	ff                   	(bad)  
    5e88:	ff                   	(bad)  
    5e89:	ff                   	(bad)  
    5e8a:	ff                   	(bad)  
    5e8b:	ff                   	(bad)  
    5e8c:	ff                   	(bad)  
    5e8d:	ff                   	(bad)  
    5e8e:	ff                   	(bad)  
    5e8f:	ff                   	(bad)  
    5e90:	ff                   	(bad)  
    5e91:	ff                   	(bad)  
    5e92:	ff                   	(bad)  
    5e93:	ff                   	(bad)  
    5e94:	ff                   	(bad)  
    5e95:	ff                   	(bad)  
    5e96:	ff                   	(bad)  
    5e97:	ff                   	(bad)  
    5e98:	ff                   	(bad)  
    5e99:	ff                   	(bad)  
    5e9a:	ff                   	(bad)  
    5e9b:	ff                   	(bad)  
    5e9c:	ff                   	(bad)  
    5e9d:	ff                   	(bad)  
    5e9e:	ff                   	(bad)  
    5e9f:	ff                   	(bad)  
    5ea0:	ff                   	(bad)  
    5ea1:	ff                   	(bad)  
    5ea2:	ff                   	(bad)  
    5ea3:	ff                   	(bad)  
    5ea4:	ff                   	(bad)  
    5ea5:	ff                   	(bad)  
    5ea6:	ff                   	(bad)  
    5ea7:	ff                   	(bad)  
    5ea8:	ff                   	(bad)  
    5ea9:	ff                   	(bad)  
    5eaa:	ff                   	(bad)  
    5eab:	ff                   	(bad)  
    5eac:	ff                   	(bad)  
    5ead:	ff                   	(bad)  
    5eae:	ff                   	(bad)  
    5eaf:	ff                   	(bad)  
    5eb0:	ff                   	(bad)  
    5eb1:	ff                   	(bad)  
    5eb2:	ff                   	(bad)  
    5eb3:	ff                   	(bad)  
    5eb4:	ff                   	(bad)  
    5eb5:	ff                   	(bad)  
    5eb6:	ff                   	(bad)  
    5eb7:	ff                   	(bad)  
    5eb8:	ff                   	(bad)  
    5eb9:	ff                   	(bad)  
    5eba:	ff                   	(bad)  
    5ebb:	ff                   	(bad)  
    5ebc:	ff                   	(bad)  
    5ebd:	ff                   	(bad)  
    5ebe:	ff                   	(bad)  
    5ebf:	ff                   	(bad)  
    5ec0:	ff                   	(bad)  
    5ec1:	ff                   	(bad)  
    5ec2:	ff                   	(bad)  
    5ec3:	ff                   	(bad)  
    5ec4:	ff                   	(bad)  
    5ec5:	ff                   	(bad)  
    5ec6:	ff                   	(bad)  
    5ec7:	ff                   	(bad)  
    5ec8:	ff                   	(bad)  
    5ec9:	ff                   	(bad)  
    5eca:	ff                   	(bad)  
    5ecb:	ff                   	(bad)  
    5ecc:	ff                   	(bad)  
    5ecd:	ff                   	(bad)  
    5ece:	ff                   	(bad)  
    5ecf:	ff                   	(bad)  
    5ed0:	ff                   	(bad)  
    5ed1:	ff                   	(bad)  
    5ed2:	ff                   	(bad)  
    5ed3:	ff                   	(bad)  
    5ed4:	ff                   	(bad)  
    5ed5:	ff                   	(bad)  
    5ed6:	ff                   	(bad)  
    5ed7:	ff                   	(bad)  
    5ed8:	ff                   	(bad)  
    5ed9:	ff                   	(bad)  
    5eda:	ff                   	(bad)  
    5edb:	ff                   	(bad)  
    5edc:	ff                   	(bad)  
    5edd:	ff                   	(bad)  
    5ede:	ff                   	(bad)  
    5edf:	ff                   	(bad)  
    5ee0:	ff                   	(bad)  
    5ee1:	ff                   	(bad)  
    5ee2:	ff                   	(bad)  
    5ee3:	ff                   	(bad)  
    5ee4:	ff                   	(bad)  
    5ee5:	ff                   	(bad)  
    5ee6:	ff                   	(bad)  
    5ee7:	ff                   	(bad)  
    5ee8:	ff                   	(bad)  
    5ee9:	ff                   	(bad)  
    5eea:	ff                   	(bad)  
    5eeb:	ff                   	(bad)  
    5eec:	ff                   	(bad)  
    5eed:	ff                   	(bad)  
    5eee:	ff                   	(bad)  
    5eef:	ff                   	(bad)  
    5ef0:	ff                   	(bad)  
    5ef1:	ff                   	(bad)  
    5ef2:	ff                   	(bad)  
    5ef3:	ff                   	(bad)  
    5ef4:	ff                   	(bad)  
    5ef5:	ff                   	(bad)  
    5ef6:	ff                   	(bad)  
    5ef7:	ff                   	(bad)  
    5ef8:	ff                   	(bad)  
    5ef9:	ff                   	(bad)  
    5efa:	ff                   	(bad)  
    5efb:	ff                   	(bad)  
    5efc:	ff                   	(bad)  
    5efd:	ff                   	(bad)  
    5efe:	ff                   	(bad)  
    5eff:	ff                   	(bad)  
    5f00:	ff                   	(bad)  
    5f01:	ff                   	(bad)  
    5f02:	ff                   	(bad)  
    5f03:	ff                   	(bad)  
    5f04:	ff                   	(bad)  
    5f05:	ff                   	(bad)  
    5f06:	ff                   	(bad)  
    5f07:	ff                   	(bad)  
    5f08:	ff                   	(bad)  
    5f09:	ff                   	(bad)  
    5f0a:	ff                   	(bad)  
    5f0b:	ff                   	(bad)  
    5f0c:	ff                   	(bad)  
    5f0d:	ff                   	(bad)  
    5f0e:	ff                   	(bad)  
    5f0f:	ff                   	(bad)  
    5f10:	ff                   	(bad)  
    5f11:	ff                   	(bad)  
    5f12:	ff                   	(bad)  
    5f13:	ff                   	(bad)  
    5f14:	ff                   	(bad)  
    5f15:	ff                   	(bad)  
    5f16:	ff                   	(bad)  
    5f17:	ff                   	(bad)  
    5f18:	ff                   	(bad)  
    5f19:	ff                   	(bad)  
    5f1a:	ff                   	(bad)  
    5f1b:	ff                   	(bad)  
    5f1c:	ff                   	(bad)  
    5f1d:	ff                   	(bad)  
    5f1e:	ff                   	(bad)  
    5f1f:	ff                   	(bad)  
    5f20:	ff                   	(bad)  
    5f21:	ff                   	(bad)  
    5f22:	ff                   	(bad)  
    5f23:	ff                   	(bad)  
    5f24:	ff                   	(bad)  
    5f25:	ff                   	(bad)  
    5f26:	ff                   	(bad)  
    5f27:	ff                   	(bad)  
    5f28:	ff                   	(bad)  
    5f29:	ff                   	(bad)  
    5f2a:	ff                   	(bad)  
    5f2b:	ff                   	(bad)  
    5f2c:	ff                   	(bad)  
    5f2d:	ff                   	(bad)  
    5f2e:	ff                   	(bad)  
    5f2f:	ff                   	(bad)  
    5f30:	ff                   	(bad)  
    5f31:	ff                   	(bad)  
    5f32:	ff                   	(bad)  
    5f33:	ff                   	(bad)  
    5f34:	ff                   	(bad)  
    5f35:	ff                   	(bad)  
    5f36:	ff                   	(bad)  
    5f37:	ff                   	(bad)  
    5f38:	ff                   	(bad)  
    5f39:	ff                   	(bad)  
    5f3a:	ff                   	(bad)  
    5f3b:	ff                   	(bad)  
    5f3c:	ff                   	(bad)  
    5f3d:	ff                   	(bad)  
    5f3e:	ff                   	(bad)  
    5f3f:	ff                   	(bad)  
    5f40:	ff                   	(bad)  
    5f41:	ff                   	(bad)  
    5f42:	ff                   	(bad)  
    5f43:	ff                   	(bad)  
    5f44:	ff                   	(bad)  
    5f45:	ff                   	(bad)  
    5f46:	ff                   	(bad)  
    5f47:	ff                   	(bad)  
    5f48:	ff                   	(bad)  
    5f49:	ff                   	(bad)  
    5f4a:	ff                   	(bad)  
    5f4b:	ff                   	(bad)  
    5f4c:	ff                   	(bad)  
    5f4d:	ff                   	(bad)  
    5f4e:	ff                   	(bad)  
    5f4f:	ff                   	(bad)  
    5f50:	ff                   	(bad)  
    5f51:	ff                   	(bad)  
    5f52:	ff                   	(bad)  
    5f53:	ff                   	(bad)  
    5f54:	ff                   	(bad)  
    5f55:	ff                   	(bad)  
    5f56:	ff                   	(bad)  
    5f57:	ff                   	(bad)  
    5f58:	ff                   	(bad)  
    5f59:	ff                   	(bad)  
    5f5a:	ff                   	(bad)  
    5f5b:	ff                   	(bad)  
    5f5c:	ff                   	(bad)  
    5f5d:	ff                   	(bad)  
    5f5e:	ff                   	(bad)  
    5f5f:	ff                   	(bad)  
    5f60:	ff                   	(bad)  
    5f61:	ff                   	(bad)  
    5f62:	ff                   	(bad)  
    5f63:	ff                   	(bad)  
    5f64:	ff                   	(bad)  
    5f65:	ff                   	(bad)  
    5f66:	ff                   	(bad)  
    5f67:	ff                   	(bad)  
    5f68:	ff                   	(bad)  
    5f69:	ff                   	(bad)  
    5f6a:	ff                   	(bad)  
    5f6b:	ff                   	(bad)  
    5f6c:	ff                   	(bad)  
    5f6d:	ff                   	(bad)  
    5f6e:	ff                   	(bad)  
    5f6f:	ff                   	(bad)  
    5f70:	ff                   	(bad)  
    5f71:	ff                   	(bad)  
    5f72:	ff                   	(bad)  
    5f73:	ff                   	(bad)  
    5f74:	ff                   	(bad)  
    5f75:	ff                   	(bad)  
    5f76:	ff                   	(bad)  
    5f77:	ff                   	(bad)  
    5f78:	ff                   	(bad)  
    5f79:	ff                   	(bad)  
    5f7a:	ff                   	(bad)  
    5f7b:	ff                   	(bad)  
    5f7c:	ff                   	(bad)  
    5f7d:	ff                   	(bad)  
    5f7e:	ff                   	(bad)  
    5f7f:	ff                   	(bad)  
    5f80:	ff                   	(bad)  
    5f81:	ff                   	(bad)  
    5f82:	ff                   	(bad)  
    5f83:	ff                   	(bad)  
    5f84:	ff                   	(bad)  
    5f85:	ff                   	(bad)  
    5f86:	ff                   	(bad)  
    5f87:	ff                   	(bad)  
    5f88:	ff                   	(bad)  
    5f89:	ff                   	(bad)  
    5f8a:	ff                   	(bad)  
    5f8b:	ff                   	(bad)  
    5f8c:	ff                   	(bad)  
    5f8d:	ff                   	(bad)  
    5f8e:	ff                   	(bad)  
    5f8f:	ff                   	(bad)  
    5f90:	ff                   	(bad)  
    5f91:	ff                   	(bad)  
    5f92:	ff                   	(bad)  
    5f93:	ff                   	(bad)  
    5f94:	ff                   	(bad)  
    5f95:	ff                   	(bad)  
    5f96:	ff                   	(bad)  
    5f97:	ff                   	(bad)  
    5f98:	ff                   	(bad)  
    5f99:	ff                   	(bad)  
    5f9a:	ff                   	(bad)  
    5f9b:	ff                   	(bad)  
    5f9c:	ff                   	(bad)  
    5f9d:	ff                   	(bad)  
    5f9e:	ff                   	(bad)  
    5f9f:	ff                   	(bad)  
    5fa0:	ff                   	(bad)  
    5fa1:	ff                   	(bad)  
    5fa2:	ff                   	(bad)  
    5fa3:	ff                   	(bad)  
    5fa4:	ff                   	(bad)  
    5fa5:	ff                   	(bad)  
    5fa6:	ff                   	(bad)  
    5fa7:	ff                   	(bad)  
    5fa8:	ff                   	(bad)  
    5fa9:	ff                   	(bad)  
    5faa:	ff                   	(bad)  
    5fab:	ff                   	(bad)  
    5fac:	ff                   	(bad)  
    5fad:	ff                   	(bad)  
    5fae:	ff                   	(bad)  
    5faf:	ff                   	(bad)  
    5fb0:	ff                   	(bad)  
    5fb1:	ff                   	(bad)  
    5fb2:	ff                   	(bad)  
    5fb3:	ff                   	(bad)  
    5fb4:	ff                   	(bad)  
    5fb5:	ff                   	(bad)  
    5fb6:	ff                   	(bad)  
    5fb7:	ff                   	(bad)  
    5fb8:	ff                   	(bad)  
    5fb9:	ff                   	(bad)  
    5fba:	ff                   	(bad)  
    5fbb:	ff                   	(bad)  
    5fbc:	ff                   	(bad)  
    5fbd:	ff                   	(bad)  
    5fbe:	ff                   	(bad)  
    5fbf:	ff                   	(bad)  
    5fc0:	ff                   	(bad)  
    5fc1:	ff                   	(bad)  
    5fc2:	ff                   	(bad)  
    5fc3:	ff                   	(bad)  
    5fc4:	ff                   	(bad)  
    5fc5:	ff                   	(bad)  
    5fc6:	ff                   	(bad)  
    5fc7:	ff                   	(bad)  
    5fc8:	ff                   	(bad)  
    5fc9:	ff                   	(bad)  
    5fca:	ff                   	(bad)  
    5fcb:	ff                   	(bad)  
    5fcc:	ff                   	(bad)  
    5fcd:	ff                   	(bad)  
    5fce:	ff                   	(bad)  
    5fcf:	ff                   	(bad)  
    5fd0:	ff                   	(bad)  
    5fd1:	ff                   	(bad)  
    5fd2:	ff                   	(bad)  
    5fd3:	ff                   	(bad)  
    5fd4:	ff                   	(bad)  
    5fd5:	ff                   	(bad)  
    5fd6:	ff                   	(bad)  
    5fd7:	ff                   	(bad)  
    5fd8:	ff                   	(bad)  
    5fd9:	ff                   	(bad)  
    5fda:	ff                   	(bad)  
    5fdb:	ff                   	(bad)  
    5fdc:	ff                   	(bad)  
    5fdd:	ff                   	(bad)  
    5fde:	ff                   	(bad)  
    5fdf:	ff                   	(bad)  
    5fe0:	ff                   	(bad)  
    5fe1:	ff                   	(bad)  
    5fe2:	ff                   	(bad)  
    5fe3:	ff                   	(bad)  
    5fe4:	ff                   	(bad)  
    5fe5:	ff                   	(bad)  
    5fe6:	ff                   	(bad)  
    5fe7:	ff                   	(bad)  
    5fe8:	ff                   	(bad)  
    5fe9:	ff                   	(bad)  
    5fea:	ff                   	(bad)  
    5feb:	ff                   	(bad)  
    5fec:	ff                   	(bad)  
    5fed:	ff                   	(bad)  
    5fee:	ff                   	(bad)  
    5fef:	ff                   	(bad)  
    5ff0:	ff                   	(bad)  
    5ff1:	ff                   	(bad)  
    5ff2:	ff                   	(bad)  
    5ff3:	ff                   	(bad)  
    5ff4:	ff                   	(bad)  
    5ff5:	ff                   	(bad)  
    5ff6:	ff                   	(bad)  
    5ff7:	ff                   	(bad)  
    5ff8:	ff                   	(bad)  
    5ff9:	ff                   	(bad)  
    5ffa:	ff                   	(bad)  
    5ffb:	ff                   	(bad)  
    5ffc:	ff                   	(bad)  
    5ffd:	ff                   	(bad)  
    5ffe:	ff                   	(bad)  
    5fff:	ff                   	(bad)  
    6000:	ff                   	(bad)  
    6001:	ff                   	(bad)  
    6002:	ff                   	(bad)  
    6003:	ff                   	(bad)  
    6004:	ff                   	(bad)  
    6005:	ff                   	(bad)  
    6006:	ff                   	(bad)  
    6007:	ff                   	(bad)  
    6008:	ff                   	(bad)  
    6009:	ff                   	(bad)  
    600a:	ff                   	(bad)  
    600b:	ff                   	(bad)  
    600c:	ff                   	(bad)  
    600d:	ff                   	(bad)  
    600e:	ff                   	(bad)  
    600f:	ff                   	(bad)  
    6010:	ff                   	(bad)  
    6011:	ff                   	(bad)  
    6012:	ff                   	(bad)  
    6013:	ff                   	(bad)  
    6014:	ff                   	(bad)  
    6015:	ff                   	(bad)  
    6016:	ff                   	(bad)  
    6017:	ff                   	(bad)  
    6018:	ff                   	(bad)  
    6019:	ff                   	(bad)  
    601a:	ff                   	(bad)  
    601b:	ff                   	(bad)  
    601c:	ff                   	(bad)  
    601d:	ff                   	(bad)  
    601e:	ff                   	(bad)  
    601f:	ff                   	(bad)  
    6020:	ff                   	(bad)  
    6021:	ff                   	(bad)  
    6022:	ff                   	(bad)  
    6023:	ff                   	(bad)  
    6024:	ff                   	(bad)  
    6025:	ff                   	(bad)  
    6026:	ff                   	(bad)  
    6027:	ff                   	(bad)  
    6028:	ff                   	(bad)  
    6029:	ff                   	(bad)  
    602a:	ff                   	(bad)  
    602b:	ff                   	(bad)  
    602c:	ff                   	(bad)  
    602d:	ff                   	(bad)  
    602e:	ff                   	(bad)  
    602f:	ff                   	(bad)  
    6030:	ff                   	(bad)  
    6031:	ff                   	(bad)  
    6032:	ff                   	(bad)  
    6033:	ff                   	(bad)  
    6034:	ff                   	(bad)  
    6035:	ff                   	(bad)  
    6036:	ff                   	(bad)  
    6037:	ff                   	(bad)  
    6038:	ff                   	(bad)  
    6039:	ff                   	(bad)  
    603a:	ff                   	(bad)  
    603b:	ff                   	(bad)  
    603c:	ff                   	(bad)  
    603d:	ff                   	(bad)  
    603e:	ff                   	(bad)  
    603f:	ff                   	(bad)  
    6040:	ff                   	(bad)  
    6041:	ff                   	(bad)  
    6042:	ff                   	(bad)  
    6043:	ff                   	(bad)  
    6044:	ff                   	(bad)  
    6045:	ff                   	(bad)  
    6046:	ff                   	(bad)  
    6047:	ff                   	(bad)  
    6048:	ff                   	(bad)  
    6049:	ff                   	(bad)  
    604a:	ff                   	(bad)  
    604b:	ff                   	(bad)  
    604c:	ff                   	(bad)  
    604d:	ff                   	(bad)  
    604e:	ff                   	(bad)  
    604f:	ff                   	(bad)  
    6050:	ff                   	(bad)  
    6051:	ff                   	(bad)  
    6052:	ff                   	(bad)  
    6053:	ff                   	(bad)  
    6054:	ff                   	(bad)  
    6055:	ff                   	(bad)  
    6056:	ff                   	(bad)  
    6057:	ff                   	(bad)  
    6058:	ff                   	(bad)  
    6059:	ff                   	(bad)  
    605a:	ff                   	(bad)  
    605b:	ff                   	(bad)  
    605c:	ff                   	(bad)  
    605d:	ff                   	(bad)  
    605e:	ff                   	(bad)  
    605f:	ff                   	(bad)  
    6060:	ff                   	(bad)  
    6061:	ff                   	(bad)  
    6062:	ff                   	(bad)  
    6063:	ff                   	(bad)  
    6064:	ff                   	(bad)  
    6065:	ff                   	(bad)  
    6066:	ff                   	(bad)  
    6067:	ff                   	(bad)  
    6068:	ff                   	(bad)  
    6069:	ff                   	(bad)  
    606a:	ff                   	(bad)  
    606b:	ff                   	(bad)  
    606c:	ff                   	(bad)  
    606d:	ff                   	(bad)  
    606e:	ff                   	(bad)  
    606f:	ff                   	(bad)  
    6070:	ff                   	(bad)  
    6071:	ff                   	(bad)  
    6072:	ff                   	(bad)  
    6073:	ff                   	(bad)  
    6074:	ff                   	(bad)  
    6075:	ff                   	(bad)  
    6076:	ff                   	(bad)  
    6077:	ff                   	(bad)  
    6078:	ff                   	(bad)  
    6079:	ff                   	(bad)  
    607a:	ff                   	(bad)  
    607b:	ff                   	(bad)  
    607c:	ff                   	(bad)  
    607d:	ff                   	(bad)  
    607e:	ff                   	(bad)  
    607f:	ff                   	(bad)  
    6080:	ff                   	(bad)  
    6081:	ff                   	(bad)  
    6082:	ff                   	(bad)  
    6083:	ff                   	(bad)  
    6084:	ff                   	(bad)  
    6085:	ff                   	(bad)  
    6086:	ff                   	(bad)  
    6087:	ff                   	(bad)  
    6088:	ff                   	(bad)  
    6089:	ff                   	(bad)  
    608a:	ff                   	(bad)  
    608b:	ff                   	(bad)  
    608c:	ff                   	(bad)  
    608d:	ff                   	(bad)  
    608e:	ff                   	(bad)  
    608f:	ff                   	(bad)  
    6090:	ff                   	(bad)  
    6091:	ff                   	(bad)  
    6092:	ff                   	(bad)  
    6093:	ff                   	(bad)  
    6094:	ff                   	(bad)  
    6095:	ff                   	(bad)  
    6096:	ff                   	(bad)  
    6097:	ff                   	(bad)  
    6098:	ff                   	(bad)  
    6099:	ff                   	(bad)  
    609a:	ff                   	(bad)  
    609b:	ff                   	(bad)  
    609c:	ff                   	(bad)  
    609d:	ff                   	(bad)  
    609e:	ff                   	(bad)  
    609f:	ff                   	(bad)  
    60a0:	ff                   	(bad)  
    60a1:	ff                   	(bad)  
    60a2:	ff                   	(bad)  
    60a3:	ff                   	(bad)  
    60a4:	ff                   	(bad)  
    60a5:	ff                   	(bad)  
    60a6:	ff                   	(bad)  
    60a7:	ff                   	(bad)  
    60a8:	ff                   	(bad)  
    60a9:	ff                   	(bad)  
    60aa:	ff                   	(bad)  
    60ab:	ff                   	(bad)  
    60ac:	ff                   	(bad)  
    60ad:	ff                   	(bad)  
    60ae:	ff                   	(bad)  
    60af:	ff                   	(bad)  
    60b0:	ff                   	(bad)  
    60b1:	ff                   	(bad)  
    60b2:	ff                   	(bad)  
    60b3:	ff                   	(bad)  
    60b4:	ff                   	(bad)  
    60b5:	ff                   	(bad)  
    60b6:	ff                   	(bad)  
    60b7:	ff                   	(bad)  
    60b8:	ff                   	(bad)  
    60b9:	ff                   	(bad)  
    60ba:	ff                   	(bad)  
    60bb:	ff                   	(bad)  
    60bc:	ff                   	(bad)  
    60bd:	ff                   	(bad)  
    60be:	ff                   	(bad)  
    60bf:	ff                   	(bad)  
    60c0:	ff                   	(bad)  
    60c1:	ff                   	(bad)  
    60c2:	ff                   	(bad)  
    60c3:	ff                   	(bad)  
    60c4:	ff                   	(bad)  
    60c5:	ff                   	(bad)  
    60c6:	ff                   	(bad)  
    60c7:	ff                   	(bad)  
    60c8:	ff                   	(bad)  
    60c9:	ff                   	(bad)  
    60ca:	ff                   	(bad)  
    60cb:	ff                   	(bad)  
    60cc:	ff                   	(bad)  
    60cd:	ff                   	(bad)  
    60ce:	ff                   	(bad)  
    60cf:	ff                   	(bad)  
    60d0:	ff                   	(bad)  
    60d1:	ff                   	(bad)  
    60d2:	ff                   	(bad)  
    60d3:	ff                   	(bad)  
    60d4:	ff                   	(bad)  
    60d5:	ff                   	(bad)  
    60d6:	ff                   	(bad)  
    60d7:	ff                   	(bad)  
    60d8:	ff                   	(bad)  
    60d9:	ff                   	(bad)  
    60da:	ff                   	(bad)  
    60db:	ff                   	(bad)  
    60dc:	ff                   	(bad)  
    60dd:	ff                   	(bad)  
    60de:	ff                   	(bad)  
    60df:	ff                   	(bad)  
    60e0:	ff                   	(bad)  
    60e1:	ff                   	(bad)  
    60e2:	ff                   	(bad)  
    60e3:	ff                   	(bad)  
    60e4:	ff                   	(bad)  
    60e5:	ff                   	(bad)  
    60e6:	ff                   	(bad)  
    60e7:	ff                   	(bad)  
    60e8:	ff                   	(bad)  
    60e9:	ff                   	(bad)  
    60ea:	ff                   	(bad)  
    60eb:	ff                   	(bad)  
    60ec:	ff                   	(bad)  
    60ed:	ff                   	(bad)  
    60ee:	ff                   	(bad)  
    60ef:	ff                   	(bad)  
    60f0:	ff                   	(bad)  
    60f1:	ff                   	(bad)  
    60f2:	ff                   	(bad)  
    60f3:	ff                   	(bad)  
    60f4:	ff                   	(bad)  
    60f5:	ff                   	(bad)  
    60f6:	ff                   	(bad)  
    60f7:	ff                   	(bad)  
    60f8:	ff                   	(bad)  
    60f9:	ff                   	(bad)  
    60fa:	ff                   	(bad)  
    60fb:	ff                   	(bad)  
    60fc:	ff                   	(bad)  
    60fd:	ff                   	(bad)  
    60fe:	ff                   	(bad)  
    60ff:	ff                   	(bad)  
    6100:	ff                   	(bad)  
    6101:	ff                   	(bad)  
    6102:	ff                   	(bad)  
    6103:	ff                   	(bad)  
    6104:	ff                   	(bad)  
    6105:	ff                   	(bad)  
    6106:	ff                   	(bad)  
    6107:	ff                   	(bad)  
    6108:	ff                   	(bad)  
    6109:	ff                   	(bad)  
    610a:	ff                   	(bad)  
    610b:	ff                   	(bad)  
    610c:	ff                   	(bad)  
    610d:	ff                   	(bad)  
    610e:	ff                   	(bad)  
    610f:	ff                   	(bad)  
    6110:	ff                   	(bad)  
    6111:	ff                   	(bad)  
    6112:	ff                   	(bad)  
    6113:	ff                   	(bad)  
    6114:	ff                   	(bad)  
    6115:	ff                   	(bad)  
    6116:	ff                   	(bad)  
    6117:	ff                   	(bad)  
    6118:	ff                   	(bad)  
    6119:	ff                   	(bad)  
    611a:	ff                   	(bad)  
    611b:	ff                   	(bad)  
    611c:	ff                   	(bad)  
    611d:	ff                   	(bad)  
    611e:	ff                   	(bad)  
    611f:	ff                   	(bad)  
    6120:	ff                   	(bad)  
    6121:	ff                   	(bad)  
    6122:	ff                   	(bad)  
    6123:	ff                   	(bad)  
    6124:	ff                   	(bad)  
    6125:	ff                   	(bad)  
    6126:	ff                   	(bad)  
    6127:	ff                   	(bad)  
    6128:	ff                   	(bad)  
    6129:	ff                   	(bad)  
    612a:	ff                   	(bad)  
    612b:	ff                   	(bad)  
    612c:	ff                   	(bad)  
    612d:	ff                   	(bad)  
    612e:	ff                   	(bad)  
    612f:	ff                   	(bad)  
    6130:	ff                   	(bad)  
    6131:	ff                   	(bad)  
    6132:	ff                   	(bad)  
    6133:	ff                   	(bad)  
    6134:	ff                   	(bad)  
    6135:	ff                   	(bad)  
    6136:	ff                   	(bad)  
    6137:	ff                   	(bad)  
    6138:	ff                   	(bad)  
    6139:	ff                   	(bad)  
    613a:	ff                   	(bad)  
    613b:	ff                   	(bad)  
    613c:	ff                   	(bad)  
    613d:	ff                   	(bad)  
    613e:	ff                   	(bad)  
    613f:	ff                   	(bad)  
    6140:	ff                   	(bad)  
    6141:	ff                   	(bad)  
    6142:	ff                   	(bad)  
    6143:	ff                   	(bad)  
    6144:	ff                   	(bad)  
    6145:	ff                   	(bad)  
    6146:	ff                   	(bad)  
    6147:	ff                   	(bad)  
    6148:	ff                   	(bad)  
    6149:	ff                   	(bad)  
    614a:	ff                   	(bad)  
    614b:	ff                   	(bad)  
    614c:	ff                   	(bad)  
    614d:	ff                   	(bad)  
    614e:	ff                   	(bad)  
    614f:	ff                   	(bad)  
    6150:	ff                   	(bad)  
    6151:	ff                   	(bad)  
    6152:	ff                   	(bad)  
    6153:	ff                   	(bad)  
    6154:	ff                   	(bad)  
    6155:	ff                   	(bad)  
    6156:	ff                   	(bad)  
    6157:	ff                   	(bad)  
    6158:	ff                   	(bad)  
    6159:	ff                   	(bad)  
    615a:	ff                   	(bad)  
    615b:	ff                   	(bad)  
    615c:	ff                   	(bad)  
    615d:	ff                   	(bad)  
    615e:	ff                   	(bad)  
    615f:	ff                   	(bad)  
    6160:	ff                   	(bad)  
    6161:	ff                   	(bad)  
    6162:	ff                   	(bad)  
    6163:	ff                   	(bad)  
    6164:	ff                   	(bad)  
    6165:	ff                   	(bad)  
    6166:	ff                   	(bad)  
    6167:	ff                   	(bad)  
    6168:	ff                   	(bad)  
    6169:	ff                   	(bad)  
    616a:	ff                   	(bad)  
    616b:	ff                   	(bad)  
    616c:	ff                   	(bad)  
    616d:	ff                   	(bad)  
    616e:	ff                   	(bad)  
    616f:	ff                   	(bad)  
    6170:	ff                   	(bad)  
    6171:	ff                   	(bad)  
    6172:	ff                   	(bad)  
    6173:	ff                   	(bad)  
    6174:	ff                   	(bad)  
    6175:	ff                   	(bad)  
    6176:	ff                   	(bad)  
    6177:	ff                   	(bad)  
    6178:	ff                   	(bad)  
    6179:	ff                   	(bad)  
    617a:	ff                   	(bad)  
    617b:	ff                   	(bad)  
    617c:	ff                   	(bad)  
    617d:	ff                   	(bad)  
    617e:	ff                   	(bad)  
    617f:	ff                   	(bad)  
    6180:	ff                   	(bad)  
    6181:	ff                   	(bad)  
    6182:	ff                   	(bad)  
    6183:	ff                   	(bad)  
    6184:	ff                   	(bad)  
    6185:	ff                   	(bad)  
    6186:	ff                   	(bad)  
    6187:	ff                   	(bad)  
    6188:	ff                   	(bad)  
    6189:	ff                   	(bad)  
    618a:	ff                   	(bad)  
    618b:	ff                   	(bad)  
    618c:	ff                   	(bad)  
    618d:	ff                   	(bad)  
    618e:	ff                   	(bad)  
    618f:	ff                   	(bad)  
    6190:	ff                   	(bad)  
    6191:	ff                   	(bad)  
    6192:	ff                   	(bad)  
    6193:	ff                   	(bad)  
    6194:	ff                   	(bad)  
    6195:	ff                   	(bad)  
    6196:	ff                   	(bad)  
    6197:	ff                   	(bad)  
    6198:	ff                   	(bad)  
    6199:	ff                   	(bad)  
    619a:	ff                   	(bad)  
    619b:	ff                   	(bad)  
    619c:	ff                   	(bad)  
    619d:	ff                   	(bad)  
    619e:	ff                   	(bad)  
    619f:	ff                   	(bad)  
    61a0:	ff                   	(bad)  
    61a1:	ff                   	(bad)  
    61a2:	ff                   	(bad)  
    61a3:	ff                   	(bad)  
    61a4:	ff                   	(bad)  
    61a5:	ff                   	(bad)  
    61a6:	ff                   	(bad)  
    61a7:	ff                   	(bad)  
    61a8:	ff                   	(bad)  
    61a9:	ff                   	(bad)  
    61aa:	ff                   	(bad)  
    61ab:	ff                   	(bad)  
    61ac:	ff                   	(bad)  
    61ad:	ff                   	(bad)  
    61ae:	ff                   	(bad)  
    61af:	ff                   	(bad)  
    61b0:	ff                   	(bad)  
    61b1:	ff                   	(bad)  
    61b2:	ff                   	(bad)  
    61b3:	ff                   	(bad)  
    61b4:	ff                   	(bad)  
    61b5:	ff                   	(bad)  
    61b6:	ff                   	(bad)  
    61b7:	ff                   	(bad)  
    61b8:	ff                   	(bad)  
    61b9:	ff                   	(bad)  
    61ba:	ff                   	(bad)  
    61bb:	ff                   	(bad)  
    61bc:	ff                   	(bad)  
    61bd:	ff                   	(bad)  
    61be:	ff                   	(bad)  
    61bf:	ff                   	(bad)  
    61c0:	ff                   	(bad)  
    61c1:	ff                   	(bad)  
    61c2:	ff                   	(bad)  
    61c3:	ff                   	(bad)  
    61c4:	ff                   	(bad)  
    61c5:	ff                   	(bad)  
    61c6:	ff                   	(bad)  
    61c7:	ff                   	(bad)  
    61c8:	ff                   	(bad)  
    61c9:	ff                   	(bad)  
    61ca:	ff                   	(bad)  
    61cb:	ff                   	(bad)  
    61cc:	ff                   	(bad)  
    61cd:	ff                   	(bad)  
    61ce:	ff                   	(bad)  
    61cf:	ff                   	(bad)  
    61d0:	ff                   	(bad)  
    61d1:	ff                   	(bad)  
    61d2:	ff                   	(bad)  
    61d3:	ff                   	(bad)  
    61d4:	ff                   	(bad)  
    61d5:	ff                   	(bad)  
    61d6:	ff                   	(bad)  
    61d7:	ff                   	(bad)  
    61d8:	ff                   	(bad)  
    61d9:	ff                   	(bad)  
    61da:	ff                   	(bad)  
    61db:	ff                   	(bad)  
    61dc:	ff                   	(bad)  
    61dd:	ff                   	(bad)  
    61de:	ff                   	(bad)  
    61df:	ff                   	(bad)  
    61e0:	ff                   	(bad)  
    61e1:	ff                   	(bad)  
    61e2:	ff                   	(bad)  
    61e3:	ff                   	(bad)  
    61e4:	ff                   	(bad)  
    61e5:	ff                   	(bad)  
    61e6:	ff                   	(bad)  
    61e7:	ff                   	(bad)  
    61e8:	ff                   	(bad)  
    61e9:	ff                   	(bad)  
    61ea:	ff                   	(bad)  
    61eb:	ff                   	(bad)  
    61ec:	ff                   	(bad)  
    61ed:	ff                   	(bad)  
    61ee:	ff                   	(bad)  
    61ef:	ff                   	(bad)  
    61f0:	ff                   	(bad)  
    61f1:	ff                   	(bad)  
    61f2:	ff                   	(bad)  
    61f3:	ff                   	(bad)  
    61f4:	ff                   	(bad)  
    61f5:	ff                   	(bad)  
    61f6:	ff                   	(bad)  
    61f7:	ff                   	(bad)  
    61f8:	ff                   	(bad)  
    61f9:	ff                   	(bad)  
    61fa:	ff                   	(bad)  
    61fb:	ff                   	(bad)  
    61fc:	ff                   	(bad)  
    61fd:	ff                   	(bad)  
    61fe:	ff                   	(bad)  
    61ff:	ff                   	(bad)  
    6200:	ff                   	(bad)  
    6201:	ff                   	(bad)  
    6202:	ff                   	(bad)  
    6203:	ff                   	(bad)  
    6204:	ff                   	(bad)  
    6205:	ff                   	(bad)  
    6206:	ff                   	(bad)  
    6207:	ff                   	(bad)  
    6208:	ff                   	(bad)  
    6209:	ff                   	(bad)  
    620a:	ff                   	(bad)  
    620b:	ff                   	(bad)  
    620c:	ff                   	(bad)  
    620d:	ff                   	(bad)  
    620e:	ff                   	(bad)  
    620f:	ff                   	(bad)  
    6210:	ff                   	(bad)  
    6211:	ff                   	(bad)  
    6212:	ff                   	(bad)  
    6213:	ff                   	(bad)  
    6214:	ff                   	(bad)  
    6215:	ff                   	(bad)  
    6216:	ff                   	(bad)  
    6217:	ff                   	(bad)  
    6218:	ff                   	(bad)  
    6219:	ff                   	(bad)  
    621a:	ff                   	(bad)  
    621b:	ff                   	(bad)  
    621c:	ff                   	(bad)  
    621d:	ff                   	(bad)  
    621e:	ff                   	(bad)  
    621f:	ff                   	(bad)  
    6220:	ff                   	(bad)  
    6221:	ff                   	(bad)  
    6222:	ff                   	(bad)  
    6223:	ff                   	(bad)  
    6224:	ff                   	(bad)  
    6225:	ff                   	(bad)  
    6226:	ff                   	(bad)  
    6227:	ff                   	(bad)  
    6228:	ff                   	(bad)  
    6229:	ff                   	(bad)  
    622a:	ff                   	(bad)  
    622b:	ff                   	(bad)  
    622c:	ff                   	(bad)  
    622d:	ff                   	(bad)  
    622e:	ff                   	(bad)  
    622f:	ff                   	(bad)  
    6230:	ff                   	(bad)  
    6231:	ff                   	(bad)  
    6232:	ff                   	(bad)  
    6233:	ff                   	(bad)  
    6234:	ff                   	(bad)  
    6235:	ff                   	(bad)  
    6236:	ff                   	(bad)  
    6237:	ff                   	(bad)  
    6238:	ff                   	(bad)  
    6239:	ff                   	(bad)  
    623a:	ff                   	(bad)  
    623b:	ff                   	(bad)  
    623c:	ff                   	(bad)  
    623d:	ff                   	(bad)  
    623e:	ff                   	(bad)  
    623f:	ff                   	(bad)  
    6240:	ff                   	(bad)  
    6241:	ff                   	(bad)  
    6242:	ff                   	(bad)  
    6243:	ff                   	(bad)  
    6244:	ff                   	(bad)  
    6245:	ff                   	(bad)  
    6246:	ff                   	(bad)  
    6247:	ff                   	(bad)  
    6248:	ff                   	(bad)  
    6249:	ff                   	(bad)  
    624a:	ff                   	(bad)  
    624b:	ff                   	(bad)  
    624c:	ff                   	(bad)  
    624d:	ff                   	(bad)  
    624e:	ff                   	(bad)  
    624f:	ff                   	(bad)  
    6250:	ff                   	(bad)  
    6251:	ff                   	(bad)  
    6252:	ff                   	(bad)  
    6253:	ff                   	(bad)  
    6254:	ff                   	(bad)  
    6255:	ff                   	(bad)  
    6256:	ff                   	(bad)  
    6257:	ff                   	(bad)  
    6258:	ff                   	(bad)  
    6259:	ff                   	(bad)  
    625a:	ff                   	(bad)  
    625b:	ff                   	(bad)  
    625c:	ff                   	(bad)  
    625d:	ff                   	(bad)  
    625e:	ff                   	(bad)  
    625f:	ff                   	(bad)  
    6260:	ff                   	(bad)  
    6261:	ff                   	(bad)  
    6262:	ff                   	(bad)  
    6263:	ff                   	(bad)  
    6264:	ff                   	(bad)  
    6265:	ff                   	(bad)  
    6266:	ff                   	(bad)  
    6267:	ff                   	(bad)  
    6268:	ff                   	(bad)  
    6269:	ff                   	(bad)  
    626a:	ff                   	(bad)  
    626b:	ff                   	(bad)  
    626c:	ff                   	(bad)  
    626d:	ff                   	(bad)  
    626e:	ff                   	(bad)  
    626f:	ff                   	(bad)  
    6270:	ff                   	(bad)  
    6271:	ff                   	(bad)  
    6272:	ff                   	(bad)  
    6273:	ff                   	(bad)  
    6274:	ff                   	(bad)  
    6275:	ff                   	(bad)  
    6276:	ff                   	(bad)  
    6277:	ff                   	(bad)  
    6278:	ff                   	(bad)  
    6279:	ff                   	(bad)  
    627a:	ff                   	(bad)  
    627b:	ff                   	(bad)  
    627c:	ff                   	(bad)  
    627d:	ff                   	(bad)  
    627e:	ff                   	(bad)  
    627f:	ff                   	(bad)  
    6280:	ff                   	(bad)  
    6281:	ff                   	(bad)  
    6282:	ff                   	(bad)  
    6283:	ff                   	(bad)  
    6284:	ff                   	(bad)  
    6285:	ff                   	(bad)  
    6286:	ff                   	(bad)  
    6287:	ff                   	(bad)  
    6288:	ff                   	(bad)  
    6289:	ff                   	(bad)  
    628a:	ff                   	(bad)  
    628b:	ff                   	(bad)  
    628c:	ff                   	(bad)  
    628d:	ff                   	(bad)  
    628e:	ff                   	(bad)  
    628f:	ff                   	(bad)  
    6290:	ff                   	(bad)  
    6291:	ff                   	(bad)  
    6292:	ff                   	(bad)  
    6293:	ff                   	(bad)  
    6294:	ff                   	(bad)  
    6295:	ff                   	(bad)  
    6296:	ff                   	(bad)  
    6297:	ff                   	(bad)  
    6298:	ff                   	(bad)  
    6299:	ff                   	(bad)  
    629a:	ff                   	(bad)  
    629b:	ff                   	(bad)  
    629c:	ff                   	(bad)  
    629d:	ff                   	(bad)  
    629e:	ff                   	(bad)  
    629f:	ff                   	(bad)  
    62a0:	ff                   	(bad)  
    62a1:	ff                   	(bad)  
    62a2:	ff                   	(bad)  
    62a3:	ff                   	(bad)  
    62a4:	ff                   	(bad)  
    62a5:	ff                   	(bad)  
    62a6:	ff                   	(bad)  
    62a7:	ff                   	(bad)  
    62a8:	ff                   	(bad)  
    62a9:	ff                   	(bad)  
    62aa:	ff                   	(bad)  
    62ab:	ff                   	(bad)  
    62ac:	ff                   	(bad)  
    62ad:	ff                   	(bad)  
    62ae:	ff                   	(bad)  
    62af:	ff                   	(bad)  
    62b0:	ff                   	(bad)  
    62b1:	ff                   	(bad)  
    62b2:	ff                   	(bad)  
    62b3:	ff                   	(bad)  
    62b4:	ff                   	(bad)  
    62b5:	ff                   	(bad)  
    62b6:	ff                   	(bad)  
    62b7:	ff                   	(bad)  
    62b8:	ff                   	(bad)  
    62b9:	ff                   	(bad)  
    62ba:	ff                   	(bad)  
    62bb:	ff                   	(bad)  
    62bc:	ff                   	(bad)  
    62bd:	ff                   	(bad)  
    62be:	ff                   	(bad)  
    62bf:	ff                   	(bad)  
    62c0:	ff                   	(bad)  
    62c1:	ff                   	(bad)  
    62c2:	ff                   	(bad)  
    62c3:	ff                   	(bad)  
    62c4:	ff                   	(bad)  
    62c5:	ff                   	(bad)  
    62c6:	ff                   	(bad)  
    62c7:	ff                   	(bad)  
    62c8:	ff                   	(bad)  
    62c9:	ff                   	(bad)  
    62ca:	ff                   	(bad)  
    62cb:	ff                   	(bad)  
    62cc:	ff                   	(bad)  
    62cd:	ff                   	(bad)  
    62ce:	ff                   	(bad)  
    62cf:	ff                   	(bad)  
    62d0:	ff                   	(bad)  
    62d1:	ff                   	(bad)  
    62d2:	ff                   	(bad)  
    62d3:	ff                   	(bad)  
    62d4:	ff                   	(bad)  
    62d5:	ff                   	(bad)  
    62d6:	ff                   	(bad)  
    62d7:	ff                   	(bad)  
    62d8:	ff                   	(bad)  
    62d9:	ff                   	(bad)  
    62da:	ff                   	(bad)  
    62db:	ff                   	(bad)  
    62dc:	ff                   	(bad)  
    62dd:	ff                   	(bad)  
    62de:	ff                   	(bad)  
    62df:	ff                   	(bad)  
    62e0:	ff                   	(bad)  
    62e1:	ff                   	(bad)  
    62e2:	ff                   	(bad)  
    62e3:	ff                   	(bad)  
    62e4:	ff                   	(bad)  
    62e5:	ff                   	(bad)  
    62e6:	ff                   	(bad)  
    62e7:	ff                   	(bad)  
    62e8:	ff                   	(bad)  
    62e9:	ff                   	(bad)  
    62ea:	ff                   	(bad)  
    62eb:	ff                   	(bad)  
    62ec:	ff                   	(bad)  
    62ed:	ff                   	(bad)  
    62ee:	ff                   	(bad)  
    62ef:	ff                   	(bad)  
    62f0:	ff                   	(bad)  
    62f1:	ff                   	(bad)  
    62f2:	ff                   	(bad)  
    62f3:	ff                   	(bad)  
    62f4:	ff                   	(bad)  
    62f5:	ff                   	(bad)  
    62f6:	ff                   	(bad)  
    62f7:	ff                   	(bad)  
    62f8:	ff                   	(bad)  
    62f9:	ff                   	(bad)  
    62fa:	ff                   	(bad)  
    62fb:	ff                   	(bad)  
    62fc:	ff                   	(bad)  
    62fd:	ff                   	(bad)  
    62fe:	ff                   	(bad)  
    62ff:	ff                   	(bad)  
    6300:	ff                   	(bad)  
    6301:	ff                   	(bad)  
    6302:	ff                   	(bad)  
    6303:	ff                   	(bad)  
    6304:	ff                   	(bad)  
    6305:	ff                   	(bad)  
    6306:	ff                   	(bad)  
    6307:	ff                   	(bad)  
    6308:	ff                   	(bad)  
    6309:	ff                   	(bad)  
    630a:	ff                   	(bad)  
    630b:	ff                   	(bad)  
    630c:	ff                   	(bad)  
    630d:	ff                   	(bad)  
    630e:	ff                   	(bad)  
    630f:	ff                   	(bad)  
    6310:	ff                   	(bad)  
    6311:	ff                   	(bad)  
    6312:	ff                   	(bad)  
    6313:	ff                   	(bad)  
    6314:	ff                   	(bad)  
    6315:	ff                   	(bad)  
    6316:	ff                   	(bad)  
    6317:	ff                   	(bad)  
    6318:	ff                   	(bad)  
    6319:	ff                   	(bad)  
    631a:	ff                   	(bad)  
    631b:	ff                   	(bad)  
    631c:	ff                   	(bad)  
    631d:	ff                   	(bad)  
    631e:	ff                   	(bad)  
    631f:	ff                   	(bad)  
    6320:	ff                   	(bad)  
    6321:	ff                   	(bad)  
    6322:	ff                   	(bad)  
    6323:	ff                   	(bad)  
    6324:	ff                   	(bad)  
    6325:	ff                   	(bad)  
    6326:	ff                   	(bad)  
    6327:	ff                   	(bad)  
    6328:	ff                   	(bad)  
    6329:	ff                   	(bad)  
    632a:	ff                   	(bad)  
    632b:	ff                   	(bad)  
    632c:	ff                   	(bad)  
    632d:	ff                   	(bad)  
    632e:	ff                   	(bad)  
    632f:	ff                   	(bad)  
    6330:	ff                   	(bad)  
    6331:	ff                   	(bad)  
    6332:	ff                   	(bad)  
    6333:	ff                   	(bad)  
    6334:	ff                   	(bad)  
    6335:	ff                   	(bad)  
    6336:	ff                   	(bad)  
    6337:	ff                   	(bad)  
    6338:	ff                   	(bad)  
    6339:	ff                   	(bad)  
    633a:	ff                   	(bad)  
    633b:	ff                   	(bad)  
    633c:	ff                   	(bad)  
    633d:	ff                   	(bad)  
    633e:	ff                   	(bad)  
    633f:	ff                   	(bad)  
    6340:	ff                   	(bad)  
    6341:	ff                   	(bad)  
    6342:	ff                   	(bad)  
    6343:	ff                   	(bad)  
    6344:	ff                   	(bad)  
    6345:	ff                   	(bad)  
    6346:	ff                   	(bad)  
    6347:	ff                   	(bad)  
    6348:	ff                   	(bad)  
    6349:	ff                   	(bad)  
    634a:	ff                   	(bad)  
    634b:	ff                   	(bad)  
    634c:	ff                   	(bad)  
    634d:	ff                   	(bad)  
    634e:	ff                   	(bad)  
    634f:	ff                   	(bad)  
    6350:	ff                   	(bad)  
    6351:	ff                   	(bad)  
    6352:	ff                   	(bad)  
    6353:	ff                   	(bad)  
    6354:	ff                   	(bad)  
    6355:	ff                   	(bad)  
    6356:	ff                   	(bad)  
    6357:	ff                   	(bad)  
    6358:	ff                   	(bad)  
    6359:	ff                   	(bad)  
    635a:	ff                   	(bad)  
    635b:	ff                   	(bad)  
    635c:	ff                   	(bad)  
    635d:	ff                   	(bad)  
    635e:	ff                   	(bad)  
    635f:	ff                   	(bad)  
    6360:	ff                   	(bad)  
    6361:	ff                   	(bad)  
    6362:	ff                   	(bad)  
    6363:	ff                   	(bad)  
    6364:	ff                   	(bad)  
    6365:	ff                   	(bad)  
    6366:	ff                   	(bad)  
    6367:	ff                   	(bad)  
    6368:	ff                   	(bad)  
    6369:	ff                   	(bad)  
    636a:	ff                   	(bad)  
    636b:	ff                   	(bad)  
    636c:	ff                   	(bad)  
    636d:	ff                   	(bad)  
    636e:	ff                   	(bad)  
    636f:	ff                   	(bad)  
    6370:	ff                   	(bad)  
    6371:	ff                   	(bad)  
    6372:	ff                   	(bad)  
    6373:	ff                   	(bad)  
    6374:	ff                   	(bad)  
    6375:	ff                   	(bad)  
    6376:	ff                   	(bad)  
    6377:	ff                   	(bad)  
    6378:	ff                   	(bad)  
    6379:	ff                   	(bad)  
    637a:	ff                   	(bad)  
    637b:	ff                   	(bad)  
    637c:	ff                   	(bad)  
    637d:	ff                   	(bad)  
    637e:	ff                   	(bad)  
    637f:	ff                   	(bad)  
    6380:	ff                   	(bad)  
    6381:	ff                   	(bad)  
    6382:	ff                   	(bad)  
    6383:	ff                   	(bad)  
    6384:	ff                   	(bad)  
    6385:	ff                   	(bad)  
    6386:	ff                   	(bad)  
    6387:	ff                   	(bad)  
    6388:	ff                   	(bad)  
    6389:	ff                   	(bad)  
    638a:	ff                   	(bad)  
    638b:	ff                   	(bad)  
    638c:	ff                   	(bad)  
    638d:	ff                   	(bad)  
    638e:	ff                   	(bad)  
    638f:	ff                   	(bad)  
    6390:	ff                   	(bad)  
    6391:	ff                   	(bad)  
    6392:	ff                   	(bad)  
    6393:	ff                   	(bad)  
    6394:	ff                   	(bad)  
    6395:	ff                   	(bad)  
    6396:	ff                   	(bad)  
    6397:	ff                   	(bad)  
    6398:	ff                   	(bad)  
    6399:	ff                   	(bad)  
    639a:	ff                   	(bad)  
    639b:	ff                   	(bad)  
    639c:	ff                   	(bad)  
    639d:	ff                   	(bad)  
    639e:	ff                   	(bad)  
    639f:	ff                   	(bad)  
    63a0:	ff                   	(bad)  
    63a1:	ff                   	(bad)  
    63a2:	ff                   	(bad)  
    63a3:	ff                   	(bad)  
    63a4:	ff                   	(bad)  
    63a5:	ff                   	(bad)  
    63a6:	ff                   	(bad)  
    63a7:	ff                   	(bad)  
    63a8:	ff                   	(bad)  
    63a9:	ff                   	(bad)  
    63aa:	ff                   	(bad)  
    63ab:	ff                   	(bad)  
    63ac:	ff                   	(bad)  
    63ad:	ff                   	(bad)  
    63ae:	ff                   	(bad)  
    63af:	ff                   	(bad)  
    63b0:	ff                   	(bad)  
    63b1:	ff                   	(bad)  
    63b2:	ff                   	(bad)  
    63b3:	ff                   	(bad)  
    63b4:	ff                   	(bad)  
    63b5:	ff                   	(bad)  
    63b6:	ff                   	(bad)  
    63b7:	ff                   	(bad)  
    63b8:	ff                   	(bad)  
    63b9:	ff                   	(bad)  
    63ba:	ff                   	(bad)  
    63bb:	ff                   	(bad)  
    63bc:	ff                   	(bad)  
    63bd:	ff                   	(bad)  
    63be:	ff                   	(bad)  
    63bf:	ff                   	(bad)  
    63c0:	ff                   	(bad)  
    63c1:	ff                   	(bad)  
    63c2:	ff                   	(bad)  
    63c3:	ff                   	(bad)  
    63c4:	ff                   	(bad)  
    63c5:	ff                   	(bad)  
    63c6:	ff                   	(bad)  
    63c7:	ff                   	(bad)  
    63c8:	ff                   	(bad)  
    63c9:	ff                   	(bad)  
    63ca:	ff                   	(bad)  
    63cb:	ff                   	(bad)  
    63cc:	ff                   	(bad)  
    63cd:	ff                   	(bad)  
    63ce:	ff                   	(bad)  
    63cf:	ff                   	(bad)  
    63d0:	ff                   	(bad)  
    63d1:	ff                   	(bad)  
    63d2:	ff                   	(bad)  
    63d3:	ff                   	(bad)  
    63d4:	ff                   	(bad)  
    63d5:	ff                   	(bad)  
    63d6:	ff                   	(bad)  
    63d7:	ff                   	(bad)  
    63d8:	ff                   	(bad)  
    63d9:	ff                   	(bad)  
    63da:	ff                   	(bad)  
    63db:	ff                   	(bad)  
    63dc:	ff                   	(bad)  
    63dd:	ff                   	(bad)  
    63de:	ff                   	(bad)  
    63df:	ff                   	(bad)  
    63e0:	ff                   	(bad)  
    63e1:	ff                   	(bad)  
    63e2:	ff                   	(bad)  
    63e3:	ff                   	(bad)  
    63e4:	ff                   	(bad)  
    63e5:	ff                   	(bad)  
    63e6:	ff                   	(bad)  
    63e7:	ff                   	(bad)  
    63e8:	ff                   	(bad)  
    63e9:	ff                   	(bad)  
    63ea:	ff                   	(bad)  
    63eb:	ff                   	(bad)  
    63ec:	ff                   	(bad)  
    63ed:	ff                   	(bad)  
    63ee:	ff                   	(bad)  
    63ef:	ff                   	(bad)  
    63f0:	ff                   	(bad)  
    63f1:	ff                   	(bad)  
    63f2:	ff                   	(bad)  
    63f3:	ff                   	(bad)  
    63f4:	ff                   	(bad)  
    63f5:	ff                   	(bad)  
    63f6:	ff                   	(bad)  
    63f7:	ff                   	(bad)  
    63f8:	ff                   	(bad)  
    63f9:	ff                   	(bad)  
    63fa:	ff                   	(bad)  
    63fb:	ff                   	(bad)  
    63fc:	ff                   	(bad)  
    63fd:	ff                   	(bad)  
    63fe:	ff                   	(bad)  
    63ff:	ff                   	(bad)  
    6400:	ff                   	(bad)  
    6401:	ff                   	(bad)  
    6402:	ff                   	(bad)  
    6403:	ff                   	(bad)  
    6404:	ff                   	(bad)  
    6405:	ff                   	(bad)  
    6406:	ff                   	(bad)  
    6407:	ff                   	(bad)  
    6408:	ff                   	(bad)  
    6409:	ff                   	(bad)  
    640a:	ff                   	(bad)  
    640b:	ff                   	(bad)  
    640c:	ff                   	(bad)  
    640d:	ff                   	(bad)  
    640e:	ff                   	(bad)  
    640f:	ff                   	(bad)  
    6410:	ff                   	(bad)  
    6411:	ff                   	(bad)  
    6412:	ff                   	(bad)  
    6413:	ff                   	(bad)  
    6414:	ff                   	(bad)  
    6415:	ff                   	(bad)  
    6416:	ff                   	(bad)  
    6417:	ff                   	(bad)  
    6418:	ff                   	(bad)  
    6419:	ff                   	(bad)  
    641a:	ff                   	(bad)  
    641b:	ff                   	(bad)  
    641c:	ff                   	(bad)  
    641d:	ff                   	(bad)  
    641e:	ff                   	(bad)  
    641f:	ff                   	(bad)  
    6420:	ff                   	(bad)  
    6421:	ff                   	(bad)  
    6422:	ff                   	(bad)  
    6423:	ff                   	(bad)  
    6424:	ff                   	(bad)  
    6425:	ff                   	(bad)  
    6426:	ff                   	(bad)  
    6427:	ff                   	(bad)  
    6428:	ff                   	(bad)  
    6429:	ff                   	(bad)  
    642a:	ff                   	(bad)  
    642b:	ff                   	(bad)  
    642c:	ff                   	(bad)  
    642d:	ff                   	(bad)  
    642e:	ff                   	(bad)  
    642f:	ff                   	(bad)  
    6430:	ff                   	(bad)  
    6431:	ff                   	(bad)  
    6432:	ff                   	(bad)  
    6433:	ff                   	(bad)  
    6434:	ff                   	(bad)  
    6435:	ff                   	(bad)  
    6436:	ff                   	(bad)  
    6437:	ff                   	(bad)  
    6438:	ff                   	(bad)  
    6439:	ff                   	(bad)  
    643a:	ff                   	(bad)  
    643b:	ff                   	(bad)  
    643c:	ff                   	(bad)  
    643d:	ff                   	(bad)  
    643e:	ff                   	(bad)  
    643f:	ff                   	(bad)  
    6440:	ff                   	(bad)  
    6441:	ff                   	(bad)  
    6442:	ff                   	(bad)  
    6443:	ff                   	(bad)  
    6444:	ff                   	(bad)  
    6445:	ff                   	(bad)  
    6446:	ff                   	(bad)  
    6447:	ff                   	(bad)  
    6448:	ff                   	(bad)  
    6449:	ff                   	(bad)  
    644a:	ff                   	(bad)  
    644b:	ff                   	(bad)  
    644c:	ff                   	(bad)  
    644d:	ff                   	(bad)  
    644e:	ff                   	(bad)  
    644f:	ff                   	(bad)  
    6450:	ff                   	(bad)  
    6451:	ff                   	(bad)  
    6452:	ff                   	(bad)  
    6453:	ff                   	(bad)  
    6454:	ff                   	(bad)  
    6455:	ff                   	(bad)  
    6456:	ff                   	(bad)  
    6457:	ff                   	(bad)  
    6458:	ff                   	(bad)  
    6459:	ff                   	(bad)  
    645a:	ff                   	(bad)  
    645b:	ff                   	(bad)  
    645c:	ff                   	(bad)  
    645d:	ff                   	(bad)  
    645e:	ff                   	(bad)  
    645f:	ff                   	(bad)  
    6460:	ff                   	(bad)  
    6461:	ff                   	(bad)  
    6462:	ff                   	(bad)  
    6463:	ff                   	(bad)  
    6464:	ff                   	(bad)  
    6465:	ff                   	(bad)  
    6466:	ff                   	(bad)  
    6467:	ff                   	(bad)  
    6468:	ff                   	(bad)  
    6469:	ff                   	(bad)  
    646a:	ff                   	(bad)  
    646b:	ff                   	(bad)  
    646c:	ff                   	(bad)  
    646d:	ff                   	(bad)  
    646e:	ff                   	(bad)  
    646f:	ff                   	(bad)  
    6470:	ff                   	(bad)  
    6471:	ff                   	(bad)  
    6472:	ff                   	(bad)  
    6473:	ff                   	(bad)  
    6474:	ff                   	(bad)  
    6475:	ff                   	(bad)  
    6476:	ff                   	(bad)  
    6477:	ff                   	(bad)  
    6478:	ff                   	(bad)  
    6479:	ff                   	(bad)  
    647a:	ff                   	(bad)  
    647b:	ff                   	(bad)  
    647c:	ff                   	(bad)  
    647d:	ff                   	(bad)  
    647e:	ff                   	(bad)  
    647f:	ff                   	(bad)  
    6480:	ff                   	(bad)  
    6481:	ff                   	(bad)  
    6482:	ff                   	(bad)  
    6483:	ff                   	(bad)  
    6484:	ff                   	(bad)  
    6485:	ff                   	(bad)  
    6486:	ff                   	(bad)  
    6487:	ff                   	(bad)  
    6488:	ff                   	(bad)  
    6489:	ff                   	(bad)  
    648a:	ff                   	(bad)  
    648b:	ff                   	(bad)  
    648c:	ff                   	(bad)  
    648d:	ff                   	(bad)  
    648e:	ff                   	(bad)  
    648f:	ff                   	(bad)  
    6490:	ff                   	(bad)  
    6491:	ff                   	(bad)  
    6492:	ff                   	(bad)  
    6493:	ff                   	(bad)  
    6494:	ff                   	(bad)  
    6495:	ff                   	(bad)  
    6496:	ff                   	(bad)  
    6497:	ff                   	(bad)  
    6498:	ff                   	(bad)  
    6499:	ff                   	(bad)  
    649a:	ff                   	(bad)  
    649b:	ff                   	(bad)  
    649c:	ff                   	(bad)  
    649d:	ff                   	(bad)  
    649e:	ff                   	(bad)  
    649f:	ff                   	(bad)  
    64a0:	ff                   	(bad)  
    64a1:	ff                   	(bad)  
    64a2:	ff                   	(bad)  
    64a3:	ff                   	(bad)  
    64a4:	ff                   	(bad)  
    64a5:	ff                   	(bad)  
    64a6:	ff                   	(bad)  
    64a7:	ff                   	(bad)  
    64a8:	ff                   	(bad)  
    64a9:	ff                   	(bad)  
    64aa:	ff                   	(bad)  
    64ab:	ff                   	(bad)  
    64ac:	ff                   	(bad)  
    64ad:	ff                   	(bad)  
    64ae:	ff                   	(bad)  
    64af:	ff                   	(bad)  
    64b0:	ff                   	(bad)  
    64b1:	ff                   	(bad)  
    64b2:	ff                   	(bad)  
    64b3:	ff                   	(bad)  
    64b4:	ff                   	(bad)  
    64b5:	ff                   	(bad)  
    64b6:	ff                   	(bad)  
    64b7:	ff                   	(bad)  
    64b8:	ff                   	(bad)  
    64b9:	ff                   	(bad)  
    64ba:	ff                   	(bad)  
    64bb:	ff                   	(bad)  
    64bc:	ff                   	(bad)  
    64bd:	ff                   	(bad)  
    64be:	ff                   	(bad)  
    64bf:	ff                   	(bad)  
    64c0:	ff                   	(bad)  
    64c1:	ff                   	(bad)  
    64c2:	ff                   	(bad)  
    64c3:	ff                   	(bad)  
    64c4:	ff                   	(bad)  
    64c5:	ff                   	(bad)  
    64c6:	ff                   	(bad)  
    64c7:	ff                   	(bad)  
    64c8:	ff                   	(bad)  
    64c9:	ff                   	(bad)  
    64ca:	ff                   	(bad)  
    64cb:	ff                   	(bad)  
    64cc:	ff                   	(bad)  
    64cd:	ff                   	(bad)  
    64ce:	ff                   	(bad)  
    64cf:	ff                   	(bad)  
    64d0:	ff                   	(bad)  
    64d1:	ff                   	(bad)  
    64d2:	ff                   	(bad)  
    64d3:	ff                   	(bad)  
    64d4:	ff                   	(bad)  
    64d5:	ff                   	(bad)  
    64d6:	ff                   	(bad)  
    64d7:	ff                   	(bad)  
    64d8:	ff                   	(bad)  
    64d9:	ff                   	(bad)  
    64da:	ff                   	(bad)  
    64db:	ff                   	(bad)  
    64dc:	ff                   	(bad)  
    64dd:	ff                   	(bad)  
    64de:	ff                   	(bad)  
    64df:	ff                   	(bad)  
    64e0:	ff                   	(bad)  
    64e1:	ff                   	(bad)  
    64e2:	ff                   	(bad)  
    64e3:	ff                   	(bad)  
    64e4:	ff                   	(bad)  
    64e5:	ff                   	(bad)  
    64e6:	ff                   	(bad)  
    64e7:	ff                   	(bad)  
    64e8:	ff                   	(bad)  
    64e9:	ff                   	(bad)  
    64ea:	ff                   	(bad)  
    64eb:	ff                   	(bad)  
    64ec:	ff                   	(bad)  
    64ed:	ff                   	(bad)  
    64ee:	ff                   	(bad)  
    64ef:	ff                   	(bad)  
    64f0:	ff                   	(bad)  
    64f1:	ff                   	(bad)  
    64f2:	ff                   	(bad)  
    64f3:	ff                   	(bad)  
    64f4:	ff                   	(bad)  
    64f5:	ff                   	(bad)  
    64f6:	ff                   	(bad)  
    64f7:	ff                   	(bad)  
    64f8:	ff                   	(bad)  
    64f9:	ff                   	(bad)  
    64fa:	ff                   	(bad)  
    64fb:	ff                   	(bad)  
    64fc:	ff                   	(bad)  
    64fd:	ff                   	(bad)  
    64fe:	ff                   	(bad)  
    64ff:	ff                   	(bad)  
    6500:	ff                   	(bad)  
    6501:	ff                   	(bad)  
    6502:	ff                   	(bad)  
    6503:	ff                   	(bad)  
    6504:	ff                   	(bad)  
    6505:	ff                   	(bad)  
    6506:	ff                   	(bad)  
    6507:	ff                   	(bad)  
    6508:	ff                   	(bad)  
    6509:	ff                   	(bad)  
    650a:	ff                   	(bad)  
    650b:	ff                   	(bad)  
    650c:	ff                   	(bad)  
    650d:	ff                   	(bad)  
    650e:	ff                   	(bad)  
    650f:	ff                   	(bad)  
    6510:	ff                   	(bad)  
    6511:	ff                   	(bad)  
    6512:	ff                   	(bad)  
    6513:	ff                   	(bad)  
    6514:	ff                   	(bad)  
    6515:	ff                   	(bad)  
    6516:	ff                   	(bad)  
    6517:	ff                   	(bad)  
    6518:	ff                   	(bad)  
    6519:	ff                   	(bad)  
    651a:	ff                   	(bad)  
    651b:	ff                   	(bad)  
    651c:	ff                   	(bad)  
    651d:	ff                   	(bad)  
    651e:	ff                   	(bad)  
    651f:	ff                   	(bad)  
    6520:	ff                   	(bad)  
    6521:	ff                   	(bad)  
    6522:	ff                   	(bad)  
    6523:	ff                   	(bad)  
    6524:	ff                   	(bad)  
    6525:	ff                   	(bad)  
    6526:	ff                   	(bad)  
    6527:	ff                   	(bad)  
    6528:	ff                   	(bad)  
    6529:	ff                   	(bad)  
    652a:	ff                   	(bad)  
    652b:	ff                   	(bad)  
    652c:	ff                   	(bad)  
    652d:	ff                   	(bad)  
    652e:	ff                   	(bad)  
    652f:	ff                   	(bad)  
    6530:	ff                   	(bad)  
    6531:	ff                   	(bad)  
    6532:	ff                   	(bad)  
    6533:	ff                   	(bad)  
    6534:	ff                   	(bad)  
    6535:	ff                   	(bad)  
    6536:	ff                   	(bad)  
    6537:	ff                   	(bad)  
    6538:	ff                   	(bad)  
    6539:	ff                   	(bad)  
    653a:	ff                   	(bad)  
    653b:	ff                   	(bad)  
    653c:	ff                   	(bad)  
    653d:	ff                   	(bad)  
    653e:	ff                   	(bad)  
    653f:	ff                   	(bad)  
    6540:	ff                   	(bad)  
    6541:	ff                   	(bad)  
    6542:	ff                   	(bad)  
    6543:	ff                   	(bad)  
    6544:	ff                   	(bad)  
    6545:	ff                   	(bad)  
    6546:	ff                   	(bad)  
    6547:	ff                   	(bad)  
    6548:	ff                   	(bad)  
    6549:	ff                   	(bad)  
    654a:	ff                   	(bad)  
    654b:	ff                   	(bad)  
    654c:	ff                   	(bad)  
    654d:	ff                   	(bad)  
    654e:	ff                   	(bad)  
    654f:	ff                   	(bad)  
    6550:	ff                   	(bad)  
    6551:	ff                   	(bad)  
    6552:	ff                   	(bad)  
    6553:	ff                   	(bad)  
    6554:	ff                   	(bad)  
    6555:	ff                   	(bad)  
    6556:	ff                   	(bad)  
    6557:	ff                   	(bad)  
    6558:	ff                   	(bad)  
    6559:	ff                   	(bad)  
    655a:	ff                   	(bad)  
    655b:	ff                   	(bad)  
    655c:	ff                   	(bad)  
    655d:	ff                   	(bad)  
    655e:	ff                   	(bad)  
    655f:	ff                   	(bad)  
    6560:	ff                   	(bad)  
    6561:	ff                   	(bad)  
    6562:	ff                   	(bad)  
    6563:	ff                   	(bad)  
    6564:	ff                   	(bad)  
    6565:	ff                   	(bad)  
    6566:	ff                   	(bad)  
    6567:	ff                   	(bad)  
    6568:	ff                   	(bad)  
    6569:	ff                   	(bad)  
    656a:	ff                   	(bad)  
    656b:	ff                   	(bad)  
    656c:	ff                   	(bad)  
    656d:	ff                   	(bad)  
    656e:	ff                   	(bad)  
    656f:	ff                   	(bad)  
    6570:	ff                   	(bad)  
    6571:	ff                   	(bad)  
    6572:	ff                   	(bad)  
    6573:	ff                   	(bad)  
    6574:	ff                   	(bad)  
    6575:	ff                   	(bad)  
    6576:	ff                   	(bad)  
    6577:	ff                   	(bad)  
    6578:	ff                   	(bad)  
    6579:	ff                   	(bad)  
    657a:	ff                   	(bad)  
    657b:	ff                   	(bad)  
    657c:	ff                   	(bad)  
    657d:	ff                   	(bad)  
    657e:	ff                   	(bad)  
    657f:	ff                   	(bad)  
    6580:	ff                   	(bad)  
    6581:	ff                   	(bad)  
    6582:	ff                   	(bad)  
    6583:	ff                   	(bad)  
    6584:	ff                   	(bad)  
    6585:	ff                   	(bad)  
    6586:	ff                   	(bad)  
    6587:	ff                   	(bad)  
    6588:	ff                   	(bad)  
    6589:	ff                   	(bad)  
    658a:	ff                   	(bad)  
    658b:	ff                   	(bad)  
    658c:	ff                   	(bad)  
    658d:	ff                   	(bad)  
    658e:	ff                   	(bad)  
    658f:	ff                   	(bad)  
    6590:	ff                   	(bad)  
    6591:	ff                   	(bad)  
    6592:	ff                   	(bad)  
    6593:	ff                   	(bad)  
    6594:	ff                   	(bad)  
    6595:	ff                   	(bad)  
    6596:	ff                   	(bad)  
    6597:	ff                   	(bad)  
    6598:	ff                   	(bad)  
    6599:	ff                   	(bad)  
    659a:	ff                   	(bad)  
    659b:	ff                   	(bad)  
    659c:	ff                   	(bad)  
    659d:	ff                   	(bad)  
    659e:	ff                   	(bad)  
    659f:	ff                   	(bad)  
    65a0:	ff                   	(bad)  
    65a1:	ff                   	(bad)  
    65a2:	ff                   	(bad)  
    65a3:	ff                   	(bad)  
    65a4:	ff                   	(bad)  
    65a5:	ff                   	(bad)  
    65a6:	ff                   	(bad)  
    65a7:	ff                   	(bad)  
    65a8:	ff                   	(bad)  
    65a9:	ff                   	(bad)  
    65aa:	ff                   	(bad)  
    65ab:	ff                   	(bad)  
    65ac:	ff                   	(bad)  
    65ad:	ff                   	(bad)  
    65ae:	ff                   	(bad)  
    65af:	ff                   	(bad)  
    65b0:	ff                   	(bad)  
    65b1:	ff                   	(bad)  
    65b2:	ff                   	(bad)  
    65b3:	ff                   	(bad)  
    65b4:	ff                   	(bad)  
    65b5:	ff                   	(bad)  
    65b6:	ff                   	(bad)  
    65b7:	ff                   	(bad)  
    65b8:	ff                   	(bad)  
    65b9:	ff                   	(bad)  
    65ba:	ff                   	(bad)  
    65bb:	ff                   	(bad)  
    65bc:	ff                   	(bad)  
    65bd:	ff                   	(bad)  
    65be:	ff                   	(bad)  
    65bf:	ff                   	(bad)  
    65c0:	ff                   	(bad)  
    65c1:	ff                   	(bad)  
    65c2:	ff                   	(bad)  
    65c3:	ff                   	(bad)  
    65c4:	ff                   	(bad)  
    65c5:	ff                   	(bad)  
    65c6:	ff                   	(bad)  
    65c7:	ff                   	(bad)  
    65c8:	ff                   	(bad)  
    65c9:	ff                   	(bad)  
    65ca:	ff                   	(bad)  
    65cb:	ff                   	(bad)  
    65cc:	ff                   	(bad)  
    65cd:	ff                   	(bad)  
    65ce:	ff                   	(bad)  
    65cf:	ff                   	(bad)  
    65d0:	ff                   	(bad)  
    65d1:	ff                   	(bad)  
    65d2:	ff                   	(bad)  
    65d3:	ff                   	(bad)  
    65d4:	ff                   	(bad)  
    65d5:	ff                   	(bad)  
    65d6:	ff                   	(bad)  
    65d7:	ff                   	(bad)  
    65d8:	ff                   	(bad)  
    65d9:	ff                   	(bad)  
    65da:	ff                   	(bad)  
    65db:	ff                   	(bad)  
    65dc:	ff                   	(bad)  
    65dd:	ff                   	(bad)  
    65de:	ff                   	(bad)  
    65df:	ff                   	(bad)  
    65e0:	ff                   	(bad)  
    65e1:	ff                   	(bad)  
    65e2:	ff                   	(bad)  
    65e3:	ff                   	(bad)  
    65e4:	ff                   	(bad)  
    65e5:	ff                   	(bad)  
    65e6:	ff                   	(bad)  
    65e7:	ff                   	(bad)  
    65e8:	ff                   	(bad)  
    65e9:	ff                   	(bad)  
    65ea:	ff                   	(bad)  
    65eb:	ff                   	(bad)  
    65ec:	ff                   	(bad)  
    65ed:	ff                   	(bad)  
    65ee:	ff                   	(bad)  
    65ef:	ff                   	(bad)  
    65f0:	ff                   	(bad)  
    65f1:	ff                   	(bad)  
    65f2:	ff                   	(bad)  
    65f3:	ff                   	(bad)  
    65f4:	ff                   	(bad)  
    65f5:	ff                   	(bad)  
    65f6:	ff                   	(bad)  
    65f7:	ff                   	(bad)  
    65f8:	ff                   	(bad)  
    65f9:	ff                   	(bad)  
    65fa:	ff                   	(bad)  
    65fb:	ff                   	(bad)  
    65fc:	ff                   	(bad)  
    65fd:	ff                   	(bad)  
    65fe:	ff                   	(bad)  
    65ff:	ff                   	(bad)  
    6600:	ff                   	(bad)  
    6601:	ff                   	(bad)  
    6602:	ff                   	(bad)  
    6603:	ff                   	(bad)  
    6604:	ff                   	(bad)  
    6605:	ff                   	(bad)  
    6606:	ff                   	(bad)  
    6607:	ff                   	(bad)  
    6608:	ff                   	(bad)  
    6609:	ff                   	(bad)  
    660a:	ff                   	(bad)  
    660b:	ff                   	(bad)  
    660c:	ff                   	(bad)  
    660d:	ff                   	(bad)  
    660e:	ff                   	(bad)  
    660f:	ff                   	(bad)  
    6610:	ff                   	(bad)  
    6611:	ff                   	(bad)  
    6612:	ff                   	(bad)  
    6613:	ff                   	(bad)  
    6614:	ff                   	(bad)  
    6615:	ff                   	(bad)  
    6616:	ff                   	(bad)  
    6617:	ff                   	(bad)  
    6618:	ff                   	(bad)  
    6619:	ff                   	(bad)  
    661a:	ff                   	(bad)  
    661b:	ff                   	(bad)  
    661c:	ff                   	(bad)  
    661d:	ff                   	(bad)  
    661e:	ff                   	(bad)  
    661f:	ff                   	(bad)  
    6620:	ff                   	(bad)  
    6621:	ff                   	(bad)  
    6622:	ff                   	(bad)  
    6623:	ff                   	(bad)  
    6624:	ff                   	(bad)  
    6625:	ff                   	(bad)  
    6626:	ff                   	(bad)  
    6627:	ff                   	(bad)  
    6628:	ff                   	(bad)  
    6629:	ff                   	(bad)  
    662a:	ff                   	(bad)  
    662b:	ff                   	(bad)  
    662c:	ff                   	(bad)  
    662d:	ff                   	(bad)  
    662e:	ff                   	(bad)  
    662f:	ff                   	(bad)  
    6630:	ff                   	(bad)  
    6631:	ff                   	(bad)  
    6632:	ff                   	(bad)  
    6633:	ff                   	(bad)  
    6634:	ff                   	(bad)  
    6635:	ff                   	(bad)  
    6636:	ff                   	(bad)  
    6637:	ff                   	(bad)  
    6638:	ff                   	(bad)  
    6639:	ff                   	(bad)  
    663a:	ff                   	(bad)  
    663b:	ff                   	(bad)  
    663c:	ff                   	(bad)  
    663d:	ff                   	(bad)  
    663e:	ff                   	(bad)  
    663f:	ff                   	(bad)  
    6640:	ff                   	(bad)  
    6641:	ff                   	(bad)  
    6642:	ff                   	(bad)  
    6643:	ff                   	(bad)  
    6644:	ff                   	(bad)  
    6645:	ff                   	(bad)  
    6646:	ff                   	(bad)  
    6647:	ff                   	(bad)  
    6648:	ff                   	(bad)  
    6649:	ff                   	(bad)  
    664a:	ff                   	(bad)  
    664b:	ff                   	(bad)  
    664c:	ff                   	(bad)  
    664d:	ff                   	(bad)  
    664e:	ff                   	(bad)  
    664f:	ff                   	(bad)  
    6650:	ff                   	(bad)  
    6651:	ff                   	(bad)  
    6652:	ff                   	(bad)  
    6653:	ff                   	(bad)  
    6654:	ff                   	(bad)  
    6655:	ff                   	(bad)  
    6656:	ff                   	(bad)  
    6657:	ff                   	(bad)  
    6658:	ff                   	(bad)  
    6659:	ff                   	(bad)  
    665a:	ff                   	(bad)  
    665b:	ff                   	(bad)  
    665c:	ff                   	(bad)  
    665d:	ff                   	(bad)  
    665e:	ff                   	(bad)  
    665f:	ff                   	(bad)  
    6660:	ff                   	(bad)  
    6661:	ff                   	(bad)  
    6662:	ff                   	(bad)  
    6663:	ff                   	(bad)  
    6664:	ff                   	(bad)  
    6665:	ff                   	(bad)  
    6666:	ff                   	(bad)  
    6667:	ff                   	(bad)  
    6668:	ff                   	(bad)  
    6669:	ff                   	(bad)  
    666a:	ff                   	(bad)  
    666b:	ff                   	(bad)  
    666c:	ff                   	(bad)  
    666d:	ff                   	(bad)  
    666e:	ff                   	(bad)  
    666f:	ff                   	(bad)  
    6670:	ff                   	(bad)  
    6671:	ff                   	(bad)  
    6672:	ff                   	(bad)  
    6673:	ff                   	(bad)  
    6674:	ff                   	(bad)  
    6675:	ff                   	(bad)  
    6676:	ff                   	(bad)  
    6677:	ff                   	(bad)  
    6678:	ff                   	(bad)  
    6679:	ff                   	(bad)  
    667a:	ff                   	(bad)  
    667b:	ff                   	(bad)  
    667c:	ff                   	(bad)  
    667d:	ff                   	(bad)  
    667e:	ff                   	(bad)  
    667f:	ff                   	(bad)  
    6680:	ff                   	(bad)  
    6681:	ff                   	(bad)  
    6682:	ff                   	(bad)  
    6683:	ff                   	(bad)  
    6684:	ff                   	(bad)  
    6685:	ff                   	(bad)  
    6686:	ff                   	(bad)  
    6687:	ff                   	(bad)  
    6688:	ff                   	(bad)  
    6689:	ff                   	(bad)  
    668a:	ff                   	(bad)  
    668b:	ff                   	(bad)  
    668c:	ff                   	(bad)  
    668d:	ff                   	(bad)  
    668e:	ff                   	(bad)  
    668f:	ff                   	(bad)  
    6690:	ff                   	(bad)  
    6691:	ff                   	(bad)  
    6692:	ff                   	(bad)  
    6693:	ff                   	(bad)  
    6694:	ff                   	(bad)  
    6695:	ff                   	(bad)  
    6696:	ff                   	(bad)  
    6697:	ff                   	(bad)  
    6698:	ff                   	(bad)  
    6699:	ff                   	(bad)  
    669a:	ff                   	(bad)  
    669b:	ff                   	(bad)  
    669c:	ff                   	(bad)  
    669d:	ff                   	(bad)  
    669e:	ff                   	(bad)  
    669f:	ff                   	(bad)  
    66a0:	ff                   	(bad)  
    66a1:	ff                   	(bad)  
    66a2:	ff                   	(bad)  
    66a3:	ff                   	(bad)  
    66a4:	ff                   	(bad)  
    66a5:	ff                   	(bad)  
    66a6:	ff                   	(bad)  
    66a7:	ff                   	(bad)  
    66a8:	ff                   	(bad)  
    66a9:	ff                   	(bad)  
    66aa:	ff                   	(bad)  
    66ab:	ff                   	(bad)  
    66ac:	ff                   	(bad)  
    66ad:	ff                   	(bad)  
    66ae:	ff                   	(bad)  
    66af:	ff                   	(bad)  
    66b0:	ff                   	(bad)  
    66b1:	ff                   	(bad)  
    66b2:	ff                   	(bad)  
    66b3:	ff                   	(bad)  
    66b4:	ff                   	(bad)  
    66b5:	ff                   	(bad)  
    66b6:	ff                   	(bad)  
    66b7:	ff                   	(bad)  
    66b8:	ff                   	(bad)  
    66b9:	ff                   	(bad)  
    66ba:	ff                   	(bad)  
    66bb:	ff                   	(bad)  
    66bc:	ff                   	(bad)  
    66bd:	ff                   	(bad)  
    66be:	ff                   	(bad)  
    66bf:	ff                   	(bad)  
    66c0:	ff                   	(bad)  
    66c1:	ff                   	(bad)  
    66c2:	ff                   	(bad)  
    66c3:	ff                   	(bad)  
    66c4:	ff                   	(bad)  
    66c5:	ff                   	(bad)  
    66c6:	ff                   	(bad)  
    66c7:	ff                   	(bad)  
    66c8:	ff                   	(bad)  
    66c9:	ff                   	(bad)  
    66ca:	ff                   	(bad)  
    66cb:	ff                   	(bad)  
    66cc:	ff                   	(bad)  
    66cd:	ff                   	(bad)  
    66ce:	ff                   	(bad)  
    66cf:	ff                   	(bad)  
    66d0:	ff                   	(bad)  
    66d1:	ff                   	(bad)  
    66d2:	ff                   	(bad)  
    66d3:	ff                   	(bad)  
    66d4:	ff                   	(bad)  
    66d5:	ff                   	(bad)  
    66d6:	ff                   	(bad)  
    66d7:	ff                   	(bad)  
    66d8:	ff                   	(bad)  
    66d9:	ff                   	(bad)  
    66da:	ff                   	(bad)  
    66db:	ff                   	(bad)  
    66dc:	ff                   	(bad)  
    66dd:	ff                   	(bad)  
    66de:	ff                   	(bad)  
    66df:	ff                   	(bad)  
    66e0:	ff                   	(bad)  
    66e1:	ff                   	(bad)  
    66e2:	ff                   	(bad)  
    66e3:	ff                   	(bad)  
    66e4:	ff                   	(bad)  
    66e5:	ff                   	(bad)  
    66e6:	ff                   	(bad)  
    66e7:	ff                   	(bad)  
    66e8:	ff                   	(bad)  
    66e9:	ff                   	(bad)  
    66ea:	ff                   	(bad)  
    66eb:	ff                   	(bad)  
    66ec:	ff                   	(bad)  
    66ed:	ff                   	(bad)  
    66ee:	ff                   	(bad)  
    66ef:	ff                   	(bad)  
    66f0:	ff                   	(bad)  
    66f1:	ff                   	(bad)  
    66f2:	ff                   	(bad)  
    66f3:	ff                   	(bad)  
    66f4:	ff                   	(bad)  
    66f5:	ff                   	(bad)  
    66f6:	ff                   	(bad)  
    66f7:	ff                   	(bad)  
    66f8:	ff                   	(bad)  
    66f9:	ff                   	(bad)  
    66fa:	ff                   	(bad)  
    66fb:	ff                   	(bad)  
    66fc:	ff                   	(bad)  
    66fd:	ff                   	(bad)  
    66fe:	ff                   	(bad)  
    66ff:	ff                   	(bad)  
    6700:	ff                   	(bad)  
    6701:	ff                   	(bad)  
    6702:	ff                   	(bad)  
    6703:	ff                   	(bad)  
    6704:	ff                   	(bad)  
    6705:	ff                   	(bad)  
    6706:	ff                   	(bad)  
    6707:	ff                   	(bad)  
    6708:	ff                   	(bad)  
    6709:	ff                   	(bad)  
    670a:	ff                   	(bad)  
    670b:	ff                   	(bad)  
    670c:	ff                   	(bad)  
    670d:	ff                   	(bad)  
    670e:	ff                   	(bad)  
    670f:	ff                   	(bad)  
    6710:	ff                   	(bad)  
    6711:	ff                   	(bad)  
    6712:	ff                   	(bad)  
    6713:	ff                   	(bad)  
    6714:	ff                   	(bad)  
    6715:	ff                   	(bad)  
    6716:	ff                   	(bad)  
    6717:	ff                   	(bad)  
    6718:	ff                   	(bad)  
    6719:	ff                   	(bad)  
    671a:	ff                   	(bad)  
    671b:	ff                   	(bad)  
    671c:	ff                   	(bad)  
    671d:	ff                   	(bad)  
    671e:	ff                   	(bad)  
    671f:	ff                   	(bad)  
    6720:	ff                   	(bad)  
    6721:	ff                   	(bad)  
    6722:	ff                   	(bad)  
    6723:	ff                   	(bad)  
    6724:	ff                   	(bad)  
    6725:	ff                   	(bad)  
    6726:	ff                   	(bad)  
    6727:	ff                   	(bad)  
    6728:	ff                   	(bad)  
    6729:	ff                   	(bad)  
    672a:	ff                   	(bad)  
    672b:	ff                   	(bad)  
    672c:	ff                   	(bad)  
    672d:	ff                   	(bad)  
    672e:	ff                   	(bad)  
    672f:	ff                   	(bad)  
    6730:	ff                   	(bad)  
    6731:	ff                   	(bad)  
    6732:	ff                   	(bad)  
    6733:	ff                   	(bad)  
    6734:	ff                   	(bad)  
    6735:	ff                   	(bad)  
    6736:	ff                   	(bad)  
    6737:	ff                   	(bad)  
    6738:	ff                   	(bad)  
    6739:	ff                   	(bad)  
    673a:	ff                   	(bad)  
    673b:	ff                   	(bad)  
    673c:	ff                   	(bad)  
    673d:	ff                   	(bad)  
    673e:	ff                   	(bad)  
    673f:	ff                   	(bad)  
    6740:	ff                   	(bad)  
    6741:	ff                   	(bad)  
    6742:	ff                   	(bad)  
    6743:	ff                   	(bad)  
    6744:	ff                   	(bad)  
    6745:	ff                   	(bad)  
    6746:	ff                   	(bad)  
    6747:	ff                   	(bad)  
    6748:	ff                   	(bad)  
    6749:	ff                   	(bad)  
    674a:	ff                   	(bad)  
    674b:	ff                   	(bad)  
    674c:	ff                   	(bad)  
    674d:	ff                   	(bad)  
    674e:	ff                   	(bad)  
    674f:	ff                   	(bad)  
    6750:	ff                   	(bad)  
    6751:	ff                   	(bad)  
    6752:	ff                   	(bad)  
    6753:	ff                   	(bad)  
    6754:	ff                   	(bad)  
    6755:	ff                   	(bad)  
    6756:	ff                   	(bad)  
    6757:	ff                   	(bad)  
    6758:	ff                   	(bad)  
    6759:	ff                   	(bad)  
    675a:	ff                   	(bad)  
    675b:	ff                   	(bad)  
    675c:	ff                   	(bad)  
    675d:	ff                   	(bad)  
    675e:	ff                   	(bad)  
    675f:	ff                   	(bad)  
    6760:	ff                   	(bad)  
    6761:	ff                   	(bad)  
    6762:	ff                   	(bad)  
    6763:	ff                   	(bad)  
    6764:	ff                   	(bad)  
    6765:	ff                   	(bad)  
    6766:	ff                   	(bad)  
    6767:	ff                   	(bad)  
    6768:	ff                   	(bad)  
    6769:	ff                   	(bad)  
    676a:	ff                   	(bad)  
    676b:	ff                   	(bad)  
    676c:	ff                   	(bad)  
    676d:	ff                   	(bad)  
    676e:	ff                   	(bad)  
    676f:	ff                   	(bad)  
    6770:	ff                   	(bad)  
    6771:	ff                   	(bad)  
    6772:	ff                   	(bad)  
    6773:	ff                   	(bad)  
    6774:	ff                   	(bad)  
    6775:	ff                   	(bad)  
    6776:	ff                   	(bad)  
    6777:	ff                   	(bad)  
    6778:	ff                   	(bad)  
    6779:	ff                   	(bad)  
    677a:	ff                   	(bad)  
    677b:	ff                   	(bad)  
    677c:	ff                   	(bad)  
    677d:	ff                   	(bad)  
    677e:	ff                   	(bad)  
    677f:	ff                   	(bad)  
    6780:	ff                   	(bad)  
    6781:	ff                   	(bad)  
    6782:	ff                   	(bad)  
    6783:	ff                   	(bad)  
    6784:	ff                   	(bad)  
    6785:	ff                   	(bad)  
    6786:	ff                   	(bad)  
    6787:	ff                   	(bad)  
    6788:	ff                   	(bad)  
    6789:	ff                   	(bad)  
    678a:	ff                   	(bad)  
    678b:	ff                   	(bad)  
    678c:	ff                   	(bad)  
    678d:	ff                   	(bad)  
    678e:	ff                   	(bad)  
    678f:	ff                   	(bad)  
    6790:	ff                   	(bad)  
    6791:	ff                   	(bad)  
    6792:	ff                   	(bad)  
    6793:	ff                   	(bad)  
    6794:	ff                   	(bad)  
    6795:	ff                   	(bad)  
    6796:	ff                   	(bad)  
    6797:	ff                   	(bad)  
    6798:	ff                   	(bad)  
    6799:	ff                   	(bad)  
    679a:	ff                   	(bad)  
    679b:	ff                   	(bad)  
    679c:	ff                   	(bad)  
    679d:	ff                   	(bad)  
    679e:	ff                   	(bad)  
    679f:	ff                   	(bad)  
    67a0:	ff                   	(bad)  
    67a1:	ff                   	(bad)  
    67a2:	ff                   	(bad)  
    67a3:	ff                   	(bad)  
    67a4:	ff                   	(bad)  
    67a5:	ff                   	(bad)  
    67a6:	ff                   	(bad)  
    67a7:	ff                   	(bad)  
    67a8:	ff                   	(bad)  
    67a9:	ff                   	(bad)  
    67aa:	ff                   	(bad)  
    67ab:	ff                   	(bad)  
    67ac:	ff                   	(bad)  
    67ad:	ff                   	(bad)  
    67ae:	ff                   	(bad)  
    67af:	ff                   	(bad)  
    67b0:	ff                   	(bad)  
    67b1:	ff                   	(bad)  
    67b2:	ff                   	(bad)  
    67b3:	ff                   	(bad)  
    67b4:	ff                   	(bad)  
    67b5:	ff                   	(bad)  
    67b6:	ff                   	(bad)  
    67b7:	ff                   	(bad)  
    67b8:	ff                   	(bad)  
    67b9:	ff                   	(bad)  
    67ba:	ff                   	(bad)  
    67bb:	ff                   	(bad)  
    67bc:	ff                   	(bad)  
    67bd:	ff                   	(bad)  
    67be:	ff                   	(bad)  
    67bf:	ff                   	(bad)  
    67c0:	ff                   	(bad)  
    67c1:	ff                   	(bad)  
    67c2:	ff                   	(bad)  
    67c3:	ff                   	(bad)  
    67c4:	ff                   	(bad)  
    67c5:	ff                   	(bad)  
    67c6:	ff                   	(bad)  
    67c7:	ff                   	(bad)  
    67c8:	ff                   	(bad)  
    67c9:	ff                   	(bad)  
    67ca:	ff                   	(bad)  
    67cb:	ff                   	(bad)  
    67cc:	ff                   	(bad)  
    67cd:	ff                   	(bad)  
    67ce:	ff                   	(bad)  
    67cf:	ff                   	(bad)  
    67d0:	ff                   	(bad)  
    67d1:	ff                   	(bad)  
    67d2:	ff                   	(bad)  
    67d3:	ff                   	(bad)  
    67d4:	ff                   	(bad)  
    67d5:	ff                   	(bad)  
    67d6:	ff                   	(bad)  
    67d7:	ff                   	(bad)  
    67d8:	ff                   	(bad)  
    67d9:	ff                   	(bad)  
    67da:	ff                   	(bad)  
    67db:	ff                   	(bad)  
    67dc:	ff                   	(bad)  
    67dd:	ff                   	(bad)  
    67de:	ff                   	(bad)  
    67df:	ff                   	(bad)  
    67e0:	ff                   	(bad)  
    67e1:	ff                   	(bad)  
    67e2:	ff                   	(bad)  
    67e3:	ff                   	(bad)  
    67e4:	ff                   	(bad)  
    67e5:	ff                   	(bad)  
    67e6:	ff                   	(bad)  
    67e7:	ff                   	(bad)  
    67e8:	ff                   	(bad)  
    67e9:	ff                   	(bad)  
    67ea:	ff                   	(bad)  
    67eb:	ff                   	(bad)  
    67ec:	ff                   	(bad)  
    67ed:	ff                   	(bad)  
    67ee:	ff                   	(bad)  
    67ef:	ff                   	(bad)  
    67f0:	ff                   	(bad)  
    67f1:	ff                   	(bad)  
    67f2:	ff                   	(bad)  
    67f3:	ff                   	(bad)  
    67f4:	ff                   	(bad)  
    67f5:	ff                   	(bad)  
    67f6:	ff                   	(bad)  
    67f7:	ff                   	(bad)  
    67f8:	ff                   	(bad)  
    67f9:	ff                   	(bad)  
    67fa:	ff                   	(bad)  
    67fb:	ff                   	(bad)  
    67fc:	ff                   	(bad)  
    67fd:	ff                   	(bad)  
    67fe:	ff                   	(bad)  
    67ff:	ff                   	(bad)  
    6800:	ff                   	(bad)  
    6801:	ff                   	(bad)  
    6802:	ff                   	(bad)  
    6803:	ff                   	(bad)  
    6804:	ff                   	(bad)  
    6805:	ff                   	(bad)  
    6806:	ff                   	(bad)  
    6807:	ff                   	(bad)  
    6808:	ff                   	(bad)  
    6809:	ff                   	(bad)  
    680a:	ff                   	(bad)  
    680b:	ff                   	(bad)  
    680c:	ff                   	(bad)  
    680d:	ff                   	(bad)  
    680e:	ff                   	(bad)  
    680f:	ff                   	(bad)  
    6810:	ff                   	(bad)  
    6811:	ff                   	(bad)  
    6812:	ff                   	(bad)  
    6813:	ff                   	(bad)  
    6814:	ff                   	(bad)  
    6815:	ff                   	(bad)  
    6816:	ff                   	(bad)  
    6817:	ff                   	(bad)  
    6818:	ff                   	(bad)  
    6819:	ff                   	(bad)  
    681a:	ff                   	(bad)  
    681b:	ff                   	(bad)  
    681c:	ff                   	(bad)  
    681d:	ff                   	(bad)  
    681e:	ff                   	(bad)  
    681f:	ff                   	(bad)  
    6820:	ff                   	(bad)  
    6821:	ff                   	(bad)  
    6822:	ff                   	(bad)  
    6823:	ff                   	(bad)  
    6824:	ff                   	(bad)  
    6825:	ff                   	(bad)  
    6826:	ff                   	(bad)  
    6827:	ff                   	(bad)  
    6828:	ff                   	(bad)  
    6829:	ff                   	(bad)  
    682a:	ff                   	(bad)  
    682b:	ff                   	(bad)  
    682c:	ff                   	(bad)  
    682d:	ff                   	(bad)  
    682e:	ff                   	(bad)  
    682f:	ff                   	(bad)  
    6830:	ff                   	(bad)  
    6831:	ff                   	(bad)  
    6832:	ff                   	(bad)  
    6833:	ff                   	(bad)  
    6834:	ff                   	(bad)  
    6835:	ff                   	(bad)  
    6836:	ff                   	(bad)  
    6837:	ff                   	(bad)  
    6838:	ff                   	(bad)  
    6839:	ff                   	(bad)  
    683a:	ff                   	(bad)  
    683b:	ff                   	(bad)  
    683c:	ff                   	(bad)  
    683d:	ff                   	(bad)  
    683e:	ff                   	(bad)  
    683f:	ff                   	(bad)  
    6840:	ff                   	(bad)  
    6841:	ff                   	(bad)  
    6842:	ff                   	(bad)  
    6843:	ff                   	(bad)  
    6844:	ff                   	(bad)  
    6845:	ff                   	(bad)  
    6846:	ff                   	(bad)  
    6847:	ff                   	(bad)  
    6848:	ff                   	(bad)  
    6849:	ff                   	(bad)  
    684a:	ff                   	(bad)  
    684b:	ff                   	(bad)  
    684c:	ff                   	(bad)  
    684d:	ff                   	(bad)  
    684e:	ff                   	(bad)  
    684f:	ff                   	(bad)  
    6850:	ff                   	(bad)  
    6851:	ff                   	(bad)  
    6852:	ff                   	(bad)  
    6853:	ff                   	(bad)  
    6854:	ff                   	(bad)  
    6855:	ff                   	(bad)  
    6856:	ff                   	(bad)  
    6857:	ff                   	(bad)  
    6858:	ff                   	(bad)  
    6859:	ff                   	(bad)  
    685a:	ff                   	(bad)  
    685b:	ff                   	(bad)  
    685c:	ff                   	(bad)  
    685d:	ff                   	(bad)  
    685e:	ff                   	(bad)  
    685f:	ff                   	(bad)  
    6860:	ff                   	(bad)  
    6861:	ff                   	(bad)  
    6862:	ff                   	(bad)  
    6863:	ff                   	(bad)  
    6864:	ff                   	(bad)  
    6865:	ff                   	(bad)  
    6866:	ff                   	(bad)  
    6867:	ff                   	(bad)  
    6868:	ff                   	(bad)  
    6869:	ff                   	(bad)  
    686a:	ff                   	(bad)  
    686b:	ff                   	(bad)  
    686c:	ff                   	(bad)  
    686d:	ff                   	(bad)  
    686e:	ff                   	(bad)  
    686f:	ff                   	(bad)  
    6870:	ff                   	(bad)  
    6871:	ff                   	(bad)  
    6872:	ff                   	(bad)  
    6873:	ff                   	(bad)  
    6874:	ff                   	(bad)  
    6875:	ff                   	(bad)  
    6876:	ff                   	(bad)  
    6877:	ff                   	(bad)  
    6878:	ff                   	(bad)  
    6879:	ff                   	(bad)  
    687a:	ff                   	(bad)  
    687b:	ff                   	(bad)  
    687c:	ff                   	(bad)  
    687d:	ff                   	(bad)  
    687e:	ff                   	(bad)  
    687f:	ff                   	(bad)  
    6880:	ff                   	(bad)  
    6881:	ff                   	(bad)  
    6882:	ff                   	(bad)  
    6883:	ff                   	(bad)  
    6884:	ff                   	(bad)  
    6885:	ff                   	(bad)  
    6886:	ff                   	(bad)  
    6887:	ff                   	(bad)  
    6888:	ff                   	(bad)  
    6889:	ff                   	(bad)  
    688a:	ff                   	(bad)  
    688b:	ff                   	(bad)  
    688c:	ff                   	(bad)  
    688d:	ff                   	(bad)  
    688e:	ff                   	(bad)  
    688f:	ff                   	(bad)  
    6890:	ff                   	(bad)  
    6891:	ff                   	(bad)  
    6892:	ff                   	(bad)  
    6893:	ff                   	(bad)  
    6894:	ff                   	(bad)  
    6895:	ff                   	(bad)  
    6896:	ff                   	(bad)  
    6897:	ff                   	(bad)  
    6898:	ff                   	(bad)  
    6899:	ff                   	(bad)  
    689a:	ff                   	(bad)  
    689b:	ff                   	(bad)  
    689c:	ff                   	(bad)  
    689d:	ff                   	(bad)  
    689e:	ff                   	(bad)  
    689f:	ff                   	(bad)  
    68a0:	ff                   	(bad)  
    68a1:	ff                   	(bad)  
    68a2:	ff                   	(bad)  
    68a3:	ff                   	(bad)  
    68a4:	ff                   	(bad)  
    68a5:	ff                   	(bad)  
    68a6:	ff                   	(bad)  
    68a7:	ff                   	(bad)  
    68a8:	ff                   	(bad)  
    68a9:	ff                   	(bad)  
    68aa:	ff                   	(bad)  
    68ab:	ff                   	(bad)  
    68ac:	ff                   	(bad)  
    68ad:	ff                   	(bad)  
    68ae:	ff                   	(bad)  
    68af:	ff                   	(bad)  
    68b0:	ff                   	(bad)  
    68b1:	ff                   	(bad)  
    68b2:	ff                   	(bad)  
    68b3:	ff                   	(bad)  
    68b4:	ff                   	(bad)  
    68b5:	ff                   	(bad)  
    68b6:	ff                   	(bad)  
    68b7:	ff                   	(bad)  
    68b8:	ff                   	(bad)  
    68b9:	ff                   	(bad)  
    68ba:	ff                   	(bad)  
    68bb:	ff                   	(bad)  
    68bc:	ff                   	(bad)  
    68bd:	ff                   	(bad)  
    68be:	ff                   	(bad)  
    68bf:	ff                   	(bad)  
    68c0:	ff                   	(bad)  
    68c1:	ff                   	(bad)  
    68c2:	ff                   	(bad)  
    68c3:	ff                   	(bad)  
    68c4:	ff                   	(bad)  
    68c5:	ff                   	(bad)  
    68c6:	ff                   	(bad)  
    68c7:	ff                   	(bad)  
    68c8:	ff                   	(bad)  
    68c9:	ff                   	(bad)  
    68ca:	ff                   	(bad)  
    68cb:	ff                   	(bad)  
    68cc:	ff                   	(bad)  
    68cd:	ff                   	(bad)  
    68ce:	ff                   	(bad)  
    68cf:	ff                   	(bad)  
    68d0:	ff                   	(bad)  
    68d1:	ff                   	(bad)  
    68d2:	ff                   	(bad)  
    68d3:	ff                   	(bad)  
    68d4:	ff                   	(bad)  
    68d5:	ff                   	(bad)  
    68d6:	ff                   	(bad)  
    68d7:	ff                   	(bad)  
    68d8:	ff                   	(bad)  
    68d9:	ff                   	(bad)  
    68da:	ff                   	(bad)  
    68db:	ff                   	(bad)  
    68dc:	ff                   	(bad)  
    68dd:	ff                   	(bad)  
    68de:	ff                   	(bad)  
    68df:	ff                   	(bad)  
    68e0:	ff                   	(bad)  
    68e1:	ff                   	(bad)  
    68e2:	ff                   	(bad)  
    68e3:	ff                   	(bad)  
    68e4:	ff                   	(bad)  
    68e5:	ff                   	(bad)  
    68e6:	ff                   	(bad)  
    68e7:	ff                   	(bad)  
    68e8:	ff                   	(bad)  
    68e9:	ff                   	(bad)  
    68ea:	ff                   	(bad)  
    68eb:	ff                   	(bad)  
    68ec:	ff                   	(bad)  
    68ed:	ff                   	(bad)  
    68ee:	ff                   	(bad)  
    68ef:	ff                   	(bad)  
    68f0:	ff                   	(bad)  
    68f1:	ff                   	(bad)  
    68f2:	ff                   	(bad)  
    68f3:	ff                   	(bad)  
    68f4:	ff                   	(bad)  
    68f5:	ff                   	(bad)  
    68f6:	ff                   	(bad)  
    68f7:	ff                   	(bad)  
    68f8:	ff                   	(bad)  
    68f9:	ff                   	(bad)  
    68fa:	ff                   	(bad)  
    68fb:	ff                   	(bad)  
    68fc:	ff                   	(bad)  
    68fd:	ff                   	(bad)  
    68fe:	ff                   	(bad)  
    68ff:	ff                   	(bad)  
    6900:	ff                   	(bad)  
    6901:	ff                   	(bad)  
    6902:	ff                   	(bad)  
    6903:	ff                   	(bad)  
    6904:	ff                   	(bad)  
    6905:	ff                   	(bad)  
    6906:	ff                   	(bad)  
    6907:	ff                   	(bad)  
    6908:	ff                   	(bad)  
    6909:	ff                   	(bad)  
    690a:	ff                   	(bad)  
    690b:	ff                   	(bad)  
    690c:	ff                   	(bad)  
    690d:	ff                   	(bad)  
    690e:	ff                   	(bad)  
    690f:	ff                   	(bad)  
    6910:	ff                   	(bad)  
    6911:	ff                   	(bad)  
    6912:	ff                   	(bad)  
    6913:	ff                   	(bad)  
    6914:	ff                   	(bad)  
    6915:	ff                   	(bad)  
    6916:	ff                   	(bad)  
    6917:	ff                   	(bad)  
    6918:	ff                   	(bad)  
    6919:	ff                   	(bad)  
    691a:	ff                   	(bad)  
    691b:	ff                   	(bad)  
    691c:	ff                   	(bad)  
    691d:	ff                   	(bad)  
    691e:	ff                   	(bad)  
    691f:	ff                   	(bad)  
    6920:	ff                   	(bad)  
    6921:	ff                   	(bad)  
    6922:	ff                   	(bad)  
    6923:	ff                   	(bad)  
    6924:	ff                   	(bad)  
    6925:	ff                   	(bad)  
    6926:	ff                   	(bad)  
    6927:	ff                   	(bad)  
    6928:	ff                   	(bad)  
    6929:	ff                   	(bad)  
    692a:	ff                   	(bad)  
    692b:	ff                   	(bad)  
    692c:	ff                   	(bad)  
    692d:	ff                   	(bad)  
    692e:	ff                   	(bad)  
    692f:	ff                   	(bad)  
    6930:	ff                   	(bad)  
    6931:	ff                   	(bad)  
    6932:	ff                   	(bad)  
    6933:	ff                   	(bad)  
    6934:	ff                   	(bad)  
    6935:	ff                   	(bad)  
    6936:	ff                   	(bad)  
    6937:	ff                   	(bad)  
    6938:	ff                   	(bad)  
    6939:	ff                   	(bad)  
    693a:	ff                   	(bad)  
    693b:	ff                   	(bad)  
    693c:	ff                   	(bad)  
    693d:	ff                   	(bad)  
    693e:	ff                   	(bad)  
    693f:	ff                   	(bad)  
    6940:	ff                   	(bad)  
    6941:	ff                   	(bad)  
    6942:	ff                   	(bad)  
    6943:	ff                   	(bad)  
    6944:	ff                   	(bad)  
    6945:	ff                   	(bad)  
    6946:	ff                   	(bad)  
    6947:	ff                   	(bad)  
    6948:	ff                   	(bad)  
    6949:	ff                   	(bad)  
    694a:	ff                   	(bad)  
    694b:	ff                   	(bad)  
    694c:	ff                   	(bad)  
    694d:	ff                   	(bad)  
    694e:	ff                   	(bad)  
    694f:	ff                   	(bad)  
    6950:	ff                   	(bad)  
    6951:	ff                   	(bad)  
    6952:	ff                   	(bad)  
    6953:	ff                   	(bad)  
    6954:	ff                   	(bad)  
    6955:	ff                   	(bad)  
    6956:	ff                   	(bad)  
    6957:	ff                   	(bad)  
    6958:	ff                   	(bad)  
    6959:	ff                   	(bad)  
    695a:	ff                   	(bad)  
    695b:	ff                   	(bad)  
    695c:	ff                   	(bad)  
    695d:	ff                   	(bad)  
    695e:	ff                   	(bad)  
    695f:	ff                   	(bad)  
    6960:	ff                   	(bad)  
    6961:	ff                   	(bad)  
    6962:	ff                   	(bad)  
    6963:	ff                   	(bad)  
    6964:	ff                   	(bad)  
    6965:	ff                   	(bad)  
    6966:	ff                   	(bad)  
    6967:	ff                   	(bad)  
    6968:	ff                   	(bad)  
    6969:	ff                   	(bad)  
    696a:	ff                   	(bad)  
    696b:	ff                   	(bad)  
    696c:	ff                   	(bad)  
    696d:	ff                   	(bad)  
    696e:	ff                   	(bad)  
    696f:	ff                   	(bad)  
    6970:	ff                   	(bad)  
    6971:	ff                   	(bad)  
    6972:	ff                   	(bad)  
    6973:	ff                   	(bad)  
    6974:	ff                   	(bad)  
    6975:	ff                   	(bad)  
    6976:	ff                   	(bad)  
    6977:	ff                   	(bad)  
    6978:	ff                   	(bad)  
    6979:	ff                   	(bad)  
    697a:	ff                   	(bad)  
    697b:	ff                   	(bad)  
    697c:	ff                   	(bad)  
    697d:	ff                   	(bad)  
    697e:	ff                   	(bad)  
    697f:	ff                   	(bad)  
    6980:	ff                   	(bad)  
    6981:	ff                   	(bad)  
    6982:	ff                   	(bad)  
    6983:	ff                   	(bad)  
    6984:	ff                   	(bad)  
    6985:	ff                   	(bad)  
    6986:	ff                   	(bad)  
    6987:	ff                   	(bad)  
    6988:	ff                   	(bad)  
    6989:	ff                   	(bad)  
    698a:	ff                   	(bad)  
    698b:	ff                   	(bad)  
    698c:	ff                   	(bad)  
    698d:	ff                   	(bad)  
    698e:	ff                   	(bad)  
    698f:	ff                   	(bad)  
    6990:	ff                   	(bad)  
    6991:	ff                   	(bad)  
    6992:	ff                   	(bad)  
    6993:	ff                   	(bad)  
    6994:	ff                   	(bad)  
    6995:	ff                   	(bad)  
    6996:	ff                   	(bad)  
    6997:	ff                   	(bad)  
    6998:	ff                   	(bad)  
    6999:	ff                   	(bad)  
    699a:	ff                   	(bad)  
    699b:	ff                   	(bad)  
    699c:	ff                   	(bad)  
    699d:	ff                   	(bad)  
    699e:	ff                   	(bad)  
    699f:	ff                   	(bad)  
    69a0:	ff                   	(bad)  
    69a1:	ff                   	(bad)  
    69a2:	ff                   	(bad)  
    69a3:	ff                   	(bad)  
    69a4:	ff                   	(bad)  
    69a5:	ff                   	(bad)  
    69a6:	ff                   	(bad)  
    69a7:	ff                   	(bad)  
    69a8:	ff                   	(bad)  
    69a9:	ff                   	(bad)  
    69aa:	ff                   	(bad)  
    69ab:	ff                   	(bad)  
    69ac:	ff                   	(bad)  
    69ad:	ff                   	(bad)  
    69ae:	ff                   	(bad)  
    69af:	ff                   	(bad)  
    69b0:	ff                   	(bad)  
    69b1:	ff                   	(bad)  
    69b2:	ff                   	(bad)  
    69b3:	ff                   	(bad)  
    69b4:	ff                   	(bad)  
    69b5:	ff                   	(bad)  
    69b6:	ff                   	(bad)  
    69b7:	ff                   	(bad)  
    69b8:	ff                   	(bad)  
    69b9:	ff                   	(bad)  
    69ba:	ff                   	(bad)  
    69bb:	ff                   	(bad)  
    69bc:	ff                   	(bad)  
    69bd:	ff                   	(bad)  
    69be:	ff                   	(bad)  
    69bf:	ff                   	(bad)  
    69c0:	ff                   	(bad)  
    69c1:	ff                   	(bad)  
    69c2:	ff                   	(bad)  
    69c3:	ff                   	(bad)  
    69c4:	ff                   	(bad)  
    69c5:	ff                   	(bad)  
    69c6:	ff                   	(bad)  
    69c7:	ff                   	(bad)  
    69c8:	ff                   	(bad)  
    69c9:	ff                   	(bad)  
    69ca:	ff                   	(bad)  
    69cb:	ff                   	(bad)  
    69cc:	ff                   	(bad)  
    69cd:	ff                   	(bad)  
    69ce:	ff                   	(bad)  
    69cf:	ff                   	(bad)  
    69d0:	ff                   	(bad)  
    69d1:	ff                   	(bad)  
    69d2:	ff                   	(bad)  
    69d3:	ff                   	(bad)  
    69d4:	ff                   	(bad)  
    69d5:	ff                   	(bad)  
    69d6:	ff                   	(bad)  
    69d7:	ff                   	(bad)  
    69d8:	ff                   	(bad)  
    69d9:	ff                   	(bad)  
    69da:	ff                   	(bad)  
    69db:	ff                   	(bad)  
    69dc:	ff                   	(bad)  
    69dd:	ff                   	(bad)  
    69de:	ff                   	(bad)  
    69df:	ff                   	(bad)  
    69e0:	ff                   	(bad)  
    69e1:	ff                   	(bad)  
    69e2:	ff                   	(bad)  
    69e3:	ff                   	(bad)  
    69e4:	ff                   	(bad)  
    69e5:	ff                   	(bad)  
    69e6:	ff                   	(bad)  
    69e7:	ff                   	(bad)  
    69e8:	ff                   	(bad)  
    69e9:	ff                   	(bad)  
    69ea:	ff                   	(bad)  
    69eb:	ff                   	(bad)  
    69ec:	ff                   	(bad)  
    69ed:	ff                   	(bad)  
    69ee:	ff                   	(bad)  
    69ef:	ff                   	(bad)  
    69f0:	ff                   	(bad)  
    69f1:	ff                   	(bad)  
    69f2:	ff                   	(bad)  
    69f3:	ff                   	(bad)  
    69f4:	ff                   	(bad)  
    69f5:	ff                   	(bad)  
    69f6:	ff                   	(bad)  
    69f7:	ff                   	(bad)  
    69f8:	ff                   	(bad)  
    69f9:	ff                   	(bad)  
    69fa:	ff                   	(bad)  
    69fb:	ff                   	(bad)  
    69fc:	ff                   	(bad)  
    69fd:	ff                   	(bad)  
    69fe:	ff                   	(bad)  
    69ff:	ff                   	(bad)  
    6a00:	ff                   	(bad)  
    6a01:	ff                   	(bad)  
    6a02:	ff                   	(bad)  
    6a03:	ff                   	(bad)  
    6a04:	ff                   	(bad)  
    6a05:	ff                   	(bad)  
    6a06:	ff                   	(bad)  
    6a07:	ff                   	(bad)  
    6a08:	ff                   	(bad)  
    6a09:	ff                   	(bad)  
    6a0a:	ff                   	(bad)  
    6a0b:	ff                   	(bad)  
    6a0c:	ff                   	(bad)  
    6a0d:	ff                   	(bad)  
    6a0e:	ff                   	(bad)  
    6a0f:	ff                   	(bad)  
    6a10:	ff                   	(bad)  
    6a11:	ff                   	(bad)  
    6a12:	ff                   	(bad)  
    6a13:	ff                   	(bad)  
    6a14:	ff                   	(bad)  
    6a15:	ff                   	(bad)  
    6a16:	ff                   	(bad)  
    6a17:	ff                   	(bad)  
    6a18:	ff                   	(bad)  
    6a19:	ff                   	(bad)  
    6a1a:	ff                   	(bad)  
    6a1b:	ff                   	(bad)  
    6a1c:	ff                   	(bad)  
    6a1d:	ff                   	(bad)  
    6a1e:	ff                   	(bad)  
    6a1f:	ff                   	(bad)  
    6a20:	ff                   	(bad)  
    6a21:	ff                   	(bad)  
    6a22:	ff                   	(bad)  
    6a23:	ff                   	(bad)  
    6a24:	ff                   	(bad)  
    6a25:	ff                   	(bad)  
    6a26:	ff                   	(bad)  
    6a27:	ff                   	(bad)  
    6a28:	ff                   	(bad)  
    6a29:	ff                   	(bad)  
    6a2a:	ff                   	(bad)  
    6a2b:	ff                   	(bad)  
    6a2c:	ff                   	(bad)  
    6a2d:	ff                   	(bad)  
    6a2e:	ff                   	(bad)  
    6a2f:	ff                   	(bad)  
    6a30:	ff                   	(bad)  
    6a31:	ff                   	(bad)  
    6a32:	ff                   	(bad)  
    6a33:	ff                   	(bad)  
    6a34:	ff                   	(bad)  
    6a35:	ff                   	(bad)  
    6a36:	ff                   	(bad)  
    6a37:	ff                   	(bad)  
    6a38:	ff                   	(bad)  
    6a39:	ff                   	(bad)  
    6a3a:	ff                   	(bad)  
    6a3b:	ff                   	(bad)  
    6a3c:	ff                   	(bad)  
    6a3d:	ff                   	(bad)  
    6a3e:	ff                   	(bad)  
    6a3f:	ff                   	(bad)  
    6a40:	ff                   	(bad)  
    6a41:	ff                   	(bad)  
    6a42:	ff                   	(bad)  
    6a43:	ff                   	(bad)  
    6a44:	ff                   	(bad)  
    6a45:	ff                   	(bad)  
    6a46:	ff                   	(bad)  
    6a47:	ff                   	(bad)  
    6a48:	ff                   	(bad)  
    6a49:	ff                   	(bad)  
    6a4a:	ff                   	(bad)  
    6a4b:	ff                   	(bad)  
    6a4c:	ff                   	(bad)  
    6a4d:	ff                   	(bad)  
    6a4e:	ff                   	(bad)  
    6a4f:	ff                   	(bad)  
    6a50:	ff                   	(bad)  
    6a51:	ff                   	(bad)  
    6a52:	ff                   	(bad)  
    6a53:	ff                   	(bad)  
    6a54:	ff                   	(bad)  
    6a55:	ff                   	(bad)  
    6a56:	ff                   	(bad)  
    6a57:	ff                   	(bad)  
    6a58:	ff                   	(bad)  
    6a59:	ff                   	(bad)  
    6a5a:	ff                   	(bad)  
    6a5b:	ff                   	(bad)  
    6a5c:	ff                   	(bad)  
    6a5d:	ff                   	(bad)  
    6a5e:	ff                   	(bad)  
    6a5f:	ff                   	(bad)  
    6a60:	ff                   	(bad)  
    6a61:	ff                   	(bad)  
    6a62:	ff                   	(bad)  
    6a63:	ff                   	(bad)  
    6a64:	ff                   	(bad)  
    6a65:	ff                   	(bad)  
    6a66:	ff                   	(bad)  
    6a67:	ff                   	(bad)  
    6a68:	ff                   	(bad)  
    6a69:	ff                   	(bad)  
    6a6a:	ff                   	(bad)  
    6a6b:	ff                   	(bad)  
    6a6c:	ff                   	(bad)  
    6a6d:	ff                   	(bad)  
    6a6e:	ff                   	(bad)  
    6a6f:	ff                   	(bad)  
    6a70:	ff                   	(bad)  
    6a71:	ff                   	(bad)  
    6a72:	ff                   	(bad)  
    6a73:	ff                   	(bad)  
    6a74:	ff                   	(bad)  
    6a75:	ff                   	(bad)  
    6a76:	ff                   	(bad)  
    6a77:	ff                   	(bad)  
    6a78:	ff                   	(bad)  
    6a79:	ff                   	(bad)  
    6a7a:	ff                   	(bad)  
    6a7b:	ff                   	(bad)  
    6a7c:	ff                   	(bad)  
    6a7d:	ff                   	(bad)  
    6a7e:	ff                   	(bad)  
    6a7f:	ff                   	(bad)  
    6a80:	ff                   	(bad)  
    6a81:	ff                   	(bad)  
    6a82:	ff                   	(bad)  
    6a83:	ff                   	(bad)  
    6a84:	ff                   	(bad)  
    6a85:	ff                   	(bad)  
    6a86:	ff                   	(bad)  
    6a87:	ff                   	(bad)  
    6a88:	ff                   	(bad)  
    6a89:	ff                   	(bad)  
    6a8a:	ff                   	(bad)  
    6a8b:	ff                   	(bad)  
    6a8c:	ff                   	(bad)  
    6a8d:	ff                   	(bad)  
    6a8e:	ff                   	(bad)  
    6a8f:	ff                   	(bad)  
    6a90:	ff                   	(bad)  
    6a91:	ff                   	(bad)  
    6a92:	ff                   	(bad)  
    6a93:	ff                   	(bad)  
    6a94:	ff                   	(bad)  
    6a95:	ff                   	(bad)  
    6a96:	ff                   	(bad)  
    6a97:	ff                   	(bad)  
    6a98:	ff                   	(bad)  
    6a99:	ff                   	(bad)  
    6a9a:	ff                   	(bad)  
    6a9b:	ff                   	(bad)  
    6a9c:	ff                   	(bad)  
    6a9d:	ff                   	(bad)  
    6a9e:	ff                   	(bad)  
    6a9f:	ff                   	(bad)  
    6aa0:	ff                   	(bad)  
    6aa1:	ff                   	(bad)  
    6aa2:	ff                   	(bad)  
    6aa3:	ff                   	(bad)  
    6aa4:	ff                   	(bad)  
    6aa5:	ff                   	(bad)  
    6aa6:	ff                   	(bad)  
    6aa7:	ff                   	(bad)  
    6aa8:	ff                   	(bad)  
    6aa9:	ff                   	(bad)  
    6aaa:	ff                   	(bad)  
    6aab:	ff                   	(bad)  
    6aac:	ff                   	(bad)  
    6aad:	ff                   	(bad)  
    6aae:	ff                   	(bad)  
    6aaf:	ff                   	(bad)  
    6ab0:	ff                   	(bad)  
    6ab1:	ff                   	(bad)  
    6ab2:	ff                   	(bad)  
    6ab3:	ff                   	(bad)  
    6ab4:	ff                   	(bad)  
    6ab5:	ff                   	(bad)  
    6ab6:	ff                   	(bad)  
    6ab7:	ff                   	(bad)  
    6ab8:	ff                   	(bad)  
    6ab9:	ff                   	(bad)  
    6aba:	ff                   	(bad)  
    6abb:	ff                   	(bad)  
    6abc:	ff                   	(bad)  
    6abd:	ff                   	(bad)  
    6abe:	ff                   	(bad)  
    6abf:	ff                   	(bad)  
    6ac0:	ff                   	(bad)  
    6ac1:	ff                   	(bad)  
    6ac2:	ff                   	(bad)  
    6ac3:	ff                   	(bad)  
    6ac4:	ff                   	(bad)  
    6ac5:	ff                   	(bad)  
    6ac6:	ff                   	(bad)  
    6ac7:	ff                   	(bad)  
    6ac8:	ff                   	(bad)  
    6ac9:	ff                   	(bad)  
    6aca:	ff                   	(bad)  
    6acb:	ff                   	(bad)  
    6acc:	ff                   	(bad)  
    6acd:	ff                   	(bad)  
    6ace:	ff                   	(bad)  
    6acf:	ff                   	(bad)  
    6ad0:	ff                   	(bad)  
    6ad1:	ff                   	(bad)  
    6ad2:	ff                   	(bad)  
    6ad3:	ff                   	(bad)  
    6ad4:	ff                   	(bad)  
    6ad5:	ff                   	(bad)  
    6ad6:	ff                   	(bad)  
    6ad7:	ff                   	(bad)  
    6ad8:	ff                   	(bad)  
    6ad9:	ff                   	(bad)  
    6ada:	ff                   	(bad)  
    6adb:	ff                   	(bad)  
    6adc:	ff                   	(bad)  
    6add:	ff                   	(bad)  
    6ade:	ff                   	(bad)  
    6adf:	ff                   	(bad)  
    6ae0:	ff                   	(bad)  
    6ae1:	ff                   	(bad)  
    6ae2:	ff                   	(bad)  
    6ae3:	ff                   	(bad)  
    6ae4:	ff                   	(bad)  
    6ae5:	ff                   	(bad)  
    6ae6:	ff                   	(bad)  
    6ae7:	ff                   	(bad)  
    6ae8:	ff                   	(bad)  
    6ae9:	ff                   	(bad)  
    6aea:	ff                   	(bad)  
    6aeb:	ff                   	(bad)  
    6aec:	ff                   	(bad)  
    6aed:	ff                   	(bad)  
    6aee:	ff                   	(bad)  
    6aef:	ff                   	(bad)  
    6af0:	ff                   	(bad)  
    6af1:	ff                   	(bad)  
    6af2:	ff                   	(bad)  
    6af3:	ff                   	(bad)  
    6af4:	ff                   	(bad)  
    6af5:	ff                   	(bad)  
    6af6:	ff                   	(bad)  
    6af7:	ff                   	(bad)  
    6af8:	ff                   	(bad)  
    6af9:	ff                   	(bad)  
    6afa:	ff                   	(bad)  
    6afb:	ff                   	(bad)  
    6afc:	ff                   	(bad)  
    6afd:	ff                   	(bad)  
    6afe:	ff                   	(bad)  
    6aff:	ff                   	(bad)  
    6b00:	ff                   	(bad)  
    6b01:	ff                   	(bad)  
    6b02:	ff                   	(bad)  
    6b03:	ff                   	(bad)  
    6b04:	ff                   	(bad)  
    6b05:	ff                   	(bad)  
    6b06:	ff                   	(bad)  
    6b07:	ff                   	(bad)  
    6b08:	ff                   	(bad)  
    6b09:	ff                   	(bad)  
    6b0a:	ff                   	(bad)  
    6b0b:	ff                   	(bad)  
    6b0c:	ff                   	(bad)  
    6b0d:	ff                   	(bad)  
    6b0e:	ff                   	(bad)  
    6b0f:	ff                   	(bad)  
    6b10:	ff                   	(bad)  
    6b11:	ff                   	(bad)  
    6b12:	ff                   	(bad)  
    6b13:	ff                   	(bad)  
    6b14:	ff                   	(bad)  
    6b15:	ff                   	(bad)  
    6b16:	ff                   	(bad)  
    6b17:	ff                   	(bad)  
    6b18:	ff                   	(bad)  
    6b19:	ff                   	(bad)  
    6b1a:	ff                   	(bad)  
    6b1b:	ff                   	(bad)  
    6b1c:	ff                   	(bad)  
    6b1d:	ff                   	(bad)  
    6b1e:	ff                   	(bad)  
    6b1f:	ff                   	(bad)  
    6b20:	ff                   	(bad)  
    6b21:	ff                   	(bad)  
    6b22:	ff                   	(bad)  
    6b23:	ff                   	(bad)  
    6b24:	ff                   	(bad)  
    6b25:	ff                   	(bad)  
    6b26:	ff                   	(bad)  
    6b27:	ff                   	(bad)  
    6b28:	ff                   	(bad)  
    6b29:	ff                   	(bad)  
    6b2a:	ff                   	(bad)  
    6b2b:	ff                   	(bad)  
    6b2c:	ff                   	(bad)  
    6b2d:	ff                   	(bad)  
    6b2e:	ff                   	(bad)  
    6b2f:	ff                   	(bad)  
    6b30:	ff                   	(bad)  
    6b31:	ff                   	(bad)  
    6b32:	ff                   	(bad)  
    6b33:	ff                   	(bad)  
    6b34:	ff                   	(bad)  
    6b35:	ff                   	(bad)  
    6b36:	ff                   	(bad)  
    6b37:	ff                   	(bad)  
    6b38:	ff                   	(bad)  
    6b39:	ff                   	(bad)  
    6b3a:	ff                   	(bad)  
    6b3b:	ff                   	(bad)  
    6b3c:	ff                   	(bad)  
    6b3d:	ff                   	(bad)  
    6b3e:	ff                   	(bad)  
    6b3f:	ff                   	(bad)  
    6b40:	ff                   	(bad)  
    6b41:	ff                   	(bad)  
    6b42:	ff                   	(bad)  
    6b43:	ff                   	(bad)  
    6b44:	ff                   	(bad)  
    6b45:	ff                   	(bad)  
    6b46:	ff                   	(bad)  
    6b47:	ff                   	(bad)  
    6b48:	ff                   	(bad)  
    6b49:	ff                   	(bad)  
    6b4a:	ff                   	(bad)  
    6b4b:	ff                   	(bad)  
    6b4c:	ff                   	(bad)  
    6b4d:	ff                   	(bad)  
    6b4e:	ff                   	(bad)  
    6b4f:	ff                   	(bad)  
    6b50:	ff                   	(bad)  
    6b51:	ff                   	(bad)  
    6b52:	ff                   	(bad)  
    6b53:	ff                   	(bad)  
    6b54:	ff                   	(bad)  
    6b55:	ff                   	(bad)  
    6b56:	ff                   	(bad)  
    6b57:	ff                   	(bad)  
    6b58:	ff                   	(bad)  
    6b59:	ff                   	(bad)  
    6b5a:	ff                   	(bad)  
    6b5b:	ff                   	(bad)  
    6b5c:	ff                   	(bad)  
    6b5d:	ff                   	(bad)  
    6b5e:	ff                   	(bad)  
    6b5f:	ff                   	(bad)  
    6b60:	ff                   	(bad)  
    6b61:	ff                   	(bad)  
    6b62:	ff                   	(bad)  
    6b63:	ff                   	(bad)  
    6b64:	ff                   	(bad)  
    6b65:	ff                   	(bad)  
    6b66:	ff                   	(bad)  
    6b67:	ff                   	(bad)  
    6b68:	ff                   	(bad)  
    6b69:	ff                   	(bad)  
    6b6a:	ff                   	(bad)  
    6b6b:	ff                   	(bad)  
    6b6c:	ff                   	(bad)  
    6b6d:	ff                   	(bad)  
    6b6e:	ff                   	(bad)  
    6b6f:	ff                   	(bad)  
    6b70:	ff                   	(bad)  
    6b71:	ff                   	(bad)  
    6b72:	ff                   	(bad)  
    6b73:	ff                   	(bad)  
    6b74:	ff                   	(bad)  
    6b75:	ff                   	(bad)  
    6b76:	ff                   	(bad)  
    6b77:	ff                   	(bad)  
    6b78:	ff                   	(bad)  
    6b79:	ff                   	(bad)  
    6b7a:	ff                   	(bad)  
    6b7b:	ff                   	(bad)  
    6b7c:	ff                   	(bad)  
    6b7d:	ff                   	(bad)  
    6b7e:	ff                   	(bad)  
    6b7f:	ff                   	(bad)  
    6b80:	ff                   	(bad)  
    6b81:	ff                   	(bad)  
    6b82:	ff                   	(bad)  
    6b83:	ff                   	(bad)  
    6b84:	ff                   	(bad)  
    6b85:	ff                   	(bad)  
    6b86:	ff                   	(bad)  
    6b87:	ff                   	(bad)  
    6b88:	ff                   	(bad)  
    6b89:	ff                   	(bad)  
    6b8a:	ff                   	(bad)  
    6b8b:	ff                   	(bad)  
    6b8c:	ff                   	(bad)  
    6b8d:	ff                   	(bad)  
    6b8e:	ff                   	(bad)  
    6b8f:	ff                   	(bad)  
    6b90:	ff                   	(bad)  
    6b91:	ff                   	(bad)  
    6b92:	ff                   	(bad)  
    6b93:	ff                   	(bad)  
    6b94:	ff                   	(bad)  
    6b95:	ff                   	(bad)  
    6b96:	ff                   	(bad)  
    6b97:	ff                   	(bad)  
    6b98:	ff                   	(bad)  
    6b99:	ff                   	(bad)  
    6b9a:	ff                   	(bad)  
    6b9b:	ff                   	(bad)  
    6b9c:	ff                   	(bad)  
    6b9d:	ff                   	(bad)  
    6b9e:	ff                   	(bad)  
    6b9f:	ff                   	(bad)  
    6ba0:	ff                   	(bad)  
    6ba1:	ff                   	(bad)  
    6ba2:	ff                   	(bad)  
    6ba3:	ff                   	(bad)  
    6ba4:	ff                   	(bad)  
    6ba5:	ff                   	(bad)  
    6ba6:	ff                   	(bad)  
    6ba7:	ff                   	(bad)  
    6ba8:	ff                   	(bad)  
    6ba9:	ff                   	(bad)  
    6baa:	ff                   	(bad)  
    6bab:	ff                   	(bad)  
    6bac:	ff                   	(bad)  
    6bad:	ff                   	(bad)  
    6bae:	ff                   	(bad)  
    6baf:	ff                   	(bad)  
    6bb0:	ff                   	(bad)  
    6bb1:	ff                   	(bad)  
    6bb2:	ff                   	(bad)  
    6bb3:	ff                   	(bad)  
    6bb4:	ff                   	(bad)  
    6bb5:	ff                   	(bad)  
    6bb6:	ff                   	(bad)  
    6bb7:	ff                   	(bad)  
    6bb8:	ff                   	(bad)  
    6bb9:	ff                   	(bad)  
    6bba:	ff                   	(bad)  
    6bbb:	ff                   	(bad)  
    6bbc:	ff                   	(bad)  
    6bbd:	ff                   	(bad)  
    6bbe:	ff                   	(bad)  
    6bbf:	ff                   	(bad)  
    6bc0:	ff                   	(bad)  
    6bc1:	ff                   	(bad)  
    6bc2:	ff                   	(bad)  
    6bc3:	ff                   	(bad)  
    6bc4:	ff                   	(bad)  
    6bc5:	ff                   	(bad)  
    6bc6:	ff                   	(bad)  
    6bc7:	ff                   	(bad)  
    6bc8:	ff                   	(bad)  
    6bc9:	ff                   	(bad)  
    6bca:	ff                   	(bad)  
    6bcb:	ff                   	(bad)  
    6bcc:	ff                   	(bad)  
    6bcd:	ff                   	(bad)  
    6bce:	ff                   	(bad)  
    6bcf:	ff                   	(bad)  
    6bd0:	ff                   	(bad)  
    6bd1:	ff                   	(bad)  
    6bd2:	ff                   	(bad)  
    6bd3:	ff                   	(bad)  
    6bd4:	ff                   	(bad)  
    6bd5:	ff                   	(bad)  
    6bd6:	ff                   	(bad)  
    6bd7:	ff                   	(bad)  
    6bd8:	ff                   	(bad)  
    6bd9:	ff                   	(bad)  
    6bda:	ff                   	(bad)  
    6bdb:	ff                   	(bad)  
    6bdc:	ff                   	(bad)  
    6bdd:	ff                   	(bad)  
    6bde:	ff                   	(bad)  
    6bdf:	ff                   	(bad)  
    6be0:	ff                   	(bad)  
    6be1:	ff                   	(bad)  
    6be2:	ff                   	(bad)  
    6be3:	ff                   	(bad)  
    6be4:	ff                   	(bad)  
    6be5:	ff                   	(bad)  
    6be6:	ff                   	(bad)  
    6be7:	ff                   	(bad)  
    6be8:	ff                   	(bad)  
    6be9:	ff                   	(bad)  
    6bea:	ff                   	(bad)  
    6beb:	ff                   	(bad)  
    6bec:	ff                   	(bad)  
    6bed:	ff                   	(bad)  
    6bee:	ff                   	(bad)  
    6bef:	ff                   	(bad)  
    6bf0:	ff                   	(bad)  
    6bf1:	ff                   	(bad)  
    6bf2:	ff                   	(bad)  
    6bf3:	ff                   	(bad)  
    6bf4:	ff                   	(bad)  
    6bf5:	ff                   	(bad)  
    6bf6:	ff                   	(bad)  
    6bf7:	ff                   	(bad)  
    6bf8:	ff                   	(bad)  
    6bf9:	ff                   	(bad)  
    6bfa:	ff                   	(bad)  
    6bfb:	ff                   	(bad)  
    6bfc:	ff                   	(bad)  
    6bfd:	ff                   	(bad)  
    6bfe:	ff                   	(bad)  
    6bff:	ff                   	(bad)  
    6c00:	ff                   	(bad)  
    6c01:	ff                   	(bad)  
    6c02:	ff                   	(bad)  
    6c03:	ff                   	(bad)  
    6c04:	ff                   	(bad)  
    6c05:	ff                   	(bad)  
    6c06:	ff                   	(bad)  
    6c07:	ff                   	(bad)  
    6c08:	ff                   	(bad)  
    6c09:	ff                   	(bad)  
    6c0a:	ff                   	(bad)  
    6c0b:	ff                   	(bad)  
    6c0c:	ff                   	(bad)  
    6c0d:	ff                   	(bad)  
    6c0e:	ff                   	(bad)  
    6c0f:	ff                   	(bad)  
    6c10:	ff                   	(bad)  
    6c11:	ff                   	(bad)  
    6c12:	ff                   	(bad)  
    6c13:	ff                   	(bad)  
    6c14:	ff                   	(bad)  
    6c15:	ff                   	(bad)  
    6c16:	ff                   	(bad)  
    6c17:	ff                   	(bad)  
    6c18:	ff                   	(bad)  
    6c19:	ff                   	(bad)  
    6c1a:	ff                   	(bad)  
    6c1b:	ff                   	(bad)  
    6c1c:	ff                   	(bad)  
    6c1d:	ff                   	(bad)  
    6c1e:	ff                   	(bad)  
    6c1f:	ff                   	(bad)  
    6c20:	ff                   	(bad)  
    6c21:	ff                   	(bad)  
    6c22:	ff                   	(bad)  
    6c23:	ff                   	(bad)  
    6c24:	ff                   	(bad)  
    6c25:	ff                   	(bad)  
    6c26:	ff                   	(bad)  
    6c27:	ff                   	(bad)  
    6c28:	ff                   	(bad)  
    6c29:	ff                   	(bad)  
    6c2a:	ff                   	(bad)  
    6c2b:	ff                   	(bad)  
    6c2c:	ff                   	(bad)  
    6c2d:	ff                   	(bad)  
    6c2e:	ff                   	(bad)  
    6c2f:	ff                   	(bad)  
    6c30:	ff                   	(bad)  
    6c31:	ff                   	(bad)  
    6c32:	ff                   	(bad)  
    6c33:	ff                   	(bad)  
    6c34:	ff                   	(bad)  
    6c35:	ff                   	(bad)  
    6c36:	ff                   	(bad)  
    6c37:	ff                   	(bad)  
    6c38:	ff                   	(bad)  
    6c39:	ff                   	(bad)  
    6c3a:	ff                   	(bad)  
    6c3b:	ff                   	(bad)  
    6c3c:	ff                   	(bad)  
    6c3d:	ff                   	(bad)  
    6c3e:	ff                   	(bad)  
    6c3f:	ff                   	(bad)  
    6c40:	ff                   	(bad)  
    6c41:	ff                   	(bad)  
    6c42:	ff                   	(bad)  
    6c43:	ff                   	(bad)  
    6c44:	ff                   	(bad)  
    6c45:	ff                   	(bad)  
    6c46:	ff                   	(bad)  
    6c47:	ff                   	(bad)  
    6c48:	ff                   	(bad)  
    6c49:	ff                   	(bad)  
    6c4a:	ff                   	(bad)  
    6c4b:	ff                   	(bad)  
    6c4c:	ff                   	(bad)  
    6c4d:	ff                   	(bad)  
    6c4e:	ff                   	(bad)  
    6c4f:	ff                   	(bad)  
    6c50:	ff                   	(bad)  
    6c51:	ff                   	(bad)  
    6c52:	ff                   	(bad)  
    6c53:	ff                   	(bad)  
    6c54:	ff                   	(bad)  
    6c55:	ff                   	(bad)  
    6c56:	ff                   	(bad)  
    6c57:	ff                   	(bad)  
    6c58:	ff                   	(bad)  
    6c59:	ff                   	(bad)  
    6c5a:	ff                   	(bad)  
    6c5b:	ff                   	(bad)  
    6c5c:	ff                   	(bad)  
    6c5d:	ff                   	(bad)  
    6c5e:	ff                   	(bad)  
    6c5f:	ff                   	(bad)  
    6c60:	ff                   	(bad)  
    6c61:	ff                   	(bad)  
    6c62:	ff                   	(bad)  
    6c63:	ff                   	(bad)  
    6c64:	ff                   	(bad)  
    6c65:	ff                   	(bad)  
    6c66:	ff                   	(bad)  
    6c67:	ff                   	(bad)  
    6c68:	ff                   	(bad)  
    6c69:	ff                   	(bad)  
    6c6a:	ff                   	(bad)  
    6c6b:	ff                   	(bad)  
    6c6c:	ff                   	(bad)  
    6c6d:	ff                   	(bad)  
    6c6e:	ff                   	(bad)  
    6c6f:	ff                   	(bad)  
    6c70:	ff                   	(bad)  
    6c71:	ff                   	(bad)  
    6c72:	ff                   	(bad)  
    6c73:	ff                   	(bad)  
    6c74:	ff                   	(bad)  
    6c75:	ff                   	(bad)  
    6c76:	ff                   	(bad)  
    6c77:	ff                   	(bad)  
    6c78:	ff                   	(bad)  
    6c79:	ff                   	(bad)  
    6c7a:	ff                   	(bad)  
    6c7b:	ff                   	(bad)  
    6c7c:	ff                   	(bad)  
    6c7d:	ff                   	(bad)  
    6c7e:	ff                   	(bad)  
    6c7f:	ff                   	(bad)  
    6c80:	ff                   	(bad)  
    6c81:	ff                   	(bad)  
    6c82:	ff                   	(bad)  
    6c83:	ff                   	(bad)  
    6c84:	ff                   	(bad)  
    6c85:	ff                   	(bad)  
    6c86:	ff                   	(bad)  
    6c87:	ff                   	(bad)  
    6c88:	ff                   	(bad)  
    6c89:	ff                   	(bad)  
    6c8a:	ff                   	(bad)  
    6c8b:	ff                   	(bad)  
    6c8c:	ff                   	(bad)  
    6c8d:	ff                   	(bad)  
    6c8e:	ff                   	(bad)  
    6c8f:	ff                   	(bad)  
    6c90:	ff                   	(bad)  
    6c91:	ff                   	(bad)  
    6c92:	ff                   	(bad)  
    6c93:	ff                   	(bad)  
    6c94:	ff                   	(bad)  
    6c95:	ff                   	(bad)  
    6c96:	ff                   	(bad)  
    6c97:	ff                   	(bad)  
    6c98:	ff                   	(bad)  
    6c99:	ff                   	(bad)  
    6c9a:	ff                   	(bad)  
    6c9b:	ff                   	(bad)  
    6c9c:	ff                   	(bad)  
    6c9d:	ff                   	(bad)  
    6c9e:	ff                   	(bad)  
    6c9f:	ff                   	(bad)  
    6ca0:	ff                   	(bad)  
    6ca1:	ff                   	(bad)  
    6ca2:	ff                   	(bad)  
    6ca3:	ff                   	(bad)  
    6ca4:	ff                   	(bad)  
    6ca5:	ff                   	(bad)  
    6ca6:	ff                   	(bad)  
    6ca7:	ff                   	(bad)  
    6ca8:	ff                   	(bad)  
    6ca9:	ff                   	(bad)  
    6caa:	ff                   	(bad)  
    6cab:	ff                   	(bad)  
    6cac:	ff                   	(bad)  
    6cad:	ff                   	(bad)  
    6cae:	ff                   	(bad)  
    6caf:	ff                   	(bad)  
    6cb0:	ff                   	(bad)  
    6cb1:	ff                   	(bad)  
    6cb2:	ff                   	(bad)  
    6cb3:	ff                   	(bad)  
    6cb4:	ff                   	(bad)  
    6cb5:	ff                   	(bad)  
    6cb6:	ff                   	(bad)  
    6cb7:	ff                   	(bad)  
    6cb8:	ff                   	(bad)  
    6cb9:	ff                   	(bad)  
    6cba:	ff                   	(bad)  
    6cbb:	ff                   	(bad)  
    6cbc:	ff                   	(bad)  
    6cbd:	ff                   	(bad)  
    6cbe:	ff                   	(bad)  
    6cbf:	ff                   	(bad)  
    6cc0:	ff                   	(bad)  
    6cc1:	ff                   	(bad)  
    6cc2:	ff                   	(bad)  
    6cc3:	ff                   	(bad)  
    6cc4:	ff                   	(bad)  
    6cc5:	ff                   	(bad)  
    6cc6:	ff                   	(bad)  
    6cc7:	ff                   	(bad)  
    6cc8:	ff                   	(bad)  
    6cc9:	ff                   	(bad)  
    6cca:	ff                   	(bad)  
    6ccb:	ff                   	(bad)  
    6ccc:	ff                   	(bad)  
    6ccd:	ff                   	(bad)  
    6cce:	ff                   	(bad)  
    6ccf:	ff                   	(bad)  
    6cd0:	ff                   	(bad)  
    6cd1:	ff                   	(bad)  
    6cd2:	ff                   	(bad)  
    6cd3:	ff                   	(bad)  
    6cd4:	ff                   	(bad)  
    6cd5:	ff                   	(bad)  
    6cd6:	ff                   	(bad)  
    6cd7:	ff                   	(bad)  
    6cd8:	ff                   	(bad)  
    6cd9:	ff                   	(bad)  
    6cda:	ff                   	(bad)  
    6cdb:	ff                   	(bad)  
    6cdc:	ff                   	(bad)  
    6cdd:	ff                   	(bad)  
    6cde:	ff                   	(bad)  
    6cdf:	ff                   	(bad)  
    6ce0:	ff                   	(bad)  
    6ce1:	ff                   	(bad)  
    6ce2:	ff                   	(bad)  
    6ce3:	ff                   	(bad)  
    6ce4:	ff                   	(bad)  
    6ce5:	ff                   	(bad)  
    6ce6:	ff                   	(bad)  
    6ce7:	ff                   	(bad)  
    6ce8:	ff                   	(bad)  
    6ce9:	ff                   	(bad)  
    6cea:	ff                   	(bad)  
    6ceb:	ff                   	(bad)  
    6cec:	ff                   	(bad)  
    6ced:	ff                   	(bad)  
    6cee:	ff                   	(bad)  
    6cef:	ff                   	(bad)  
    6cf0:	ff                   	(bad)  
    6cf1:	ff                   	(bad)  
    6cf2:	ff                   	(bad)  
    6cf3:	ff                   	(bad)  
    6cf4:	ff                   	(bad)  
    6cf5:	ff                   	(bad)  
    6cf6:	ff                   	(bad)  
    6cf7:	ff                   	(bad)  
    6cf8:	ff                   	(bad)  
    6cf9:	ff                   	(bad)  
    6cfa:	ff                   	(bad)  
    6cfb:	ff                   	(bad)  
    6cfc:	ff                   	(bad)  
    6cfd:	ff                   	(bad)  
    6cfe:	ff                   	(bad)  
    6cff:	ff                   	(bad)  
    6d00:	ff                   	(bad)  
    6d01:	ff                   	(bad)  
    6d02:	ff                   	(bad)  
    6d03:	ff                   	(bad)  
    6d04:	ff                   	(bad)  
    6d05:	ff                   	(bad)  
    6d06:	ff                   	(bad)  
    6d07:	ff                   	(bad)  
    6d08:	ff                   	(bad)  
    6d09:	ff                   	(bad)  
    6d0a:	ff                   	(bad)  
    6d0b:	ff                   	(bad)  
    6d0c:	ff                   	(bad)  
    6d0d:	ff                   	(bad)  
    6d0e:	ff                   	(bad)  
    6d0f:	ff                   	(bad)  
    6d10:	ff                   	(bad)  
    6d11:	ff                   	(bad)  
    6d12:	ff                   	(bad)  
    6d13:	ff                   	(bad)  
    6d14:	ff                   	(bad)  
    6d15:	ff                   	(bad)  
    6d16:	ff                   	(bad)  
    6d17:	ff                   	(bad)  
    6d18:	ff                   	(bad)  
    6d19:	ff                   	(bad)  
    6d1a:	ff                   	(bad)  
    6d1b:	ff                   	(bad)  
    6d1c:	ff                   	(bad)  
    6d1d:	ff                   	(bad)  
    6d1e:	ff                   	(bad)  
    6d1f:	ff                   	(bad)  
    6d20:	ff                   	(bad)  
    6d21:	ff                   	(bad)  
    6d22:	ff                   	(bad)  
    6d23:	ff                   	(bad)  
    6d24:	ff                   	(bad)  
    6d25:	ff                   	(bad)  
    6d26:	ff                   	(bad)  
    6d27:	ff                   	(bad)  
    6d28:	ff                   	(bad)  
    6d29:	ff                   	(bad)  
    6d2a:	ff                   	(bad)  
    6d2b:	ff                   	(bad)  
    6d2c:	ff                   	(bad)  
    6d2d:	ff                   	(bad)  
    6d2e:	ff                   	(bad)  
    6d2f:	ff                   	(bad)  
    6d30:	ff                   	(bad)  
    6d31:	ff                   	(bad)  
    6d32:	ff                   	(bad)  
    6d33:	ff                   	(bad)  
    6d34:	ff                   	(bad)  
    6d35:	ff                   	(bad)  
    6d36:	ff                   	(bad)  
    6d37:	ff                   	(bad)  
    6d38:	ff                   	(bad)  
    6d39:	ff                   	(bad)  
    6d3a:	ff                   	(bad)  
    6d3b:	ff                   	(bad)  
    6d3c:	ff                   	(bad)  
    6d3d:	ff                   	(bad)  
    6d3e:	ff                   	(bad)  
    6d3f:	ff                   	(bad)  
    6d40:	ff                   	(bad)  
    6d41:	ff                   	(bad)  
    6d42:	ff                   	(bad)  
    6d43:	ff                   	(bad)  
    6d44:	ff                   	(bad)  
    6d45:	ff                   	(bad)  
    6d46:	ff                   	(bad)  
    6d47:	ff                   	(bad)  
    6d48:	ff                   	(bad)  
    6d49:	ff                   	(bad)  
    6d4a:	ff                   	(bad)  
    6d4b:	ff                   	(bad)  
    6d4c:	ff                   	(bad)  
    6d4d:	ff                   	(bad)  
    6d4e:	ff                   	(bad)  
    6d4f:	ff                   	(bad)  
    6d50:	ff                   	(bad)  
    6d51:	ff                   	(bad)  
    6d52:	ff                   	(bad)  
    6d53:	ff                   	(bad)  
    6d54:	ff                   	(bad)  
    6d55:	ff                   	(bad)  
    6d56:	ff                   	(bad)  
    6d57:	ff                   	(bad)  
    6d58:	ff                   	(bad)  
    6d59:	ff                   	(bad)  
    6d5a:	ff                   	(bad)  
    6d5b:	ff                   	(bad)  
    6d5c:	ff                   	(bad)  
    6d5d:	ff                   	(bad)  
    6d5e:	ff                   	(bad)  
    6d5f:	ff                   	(bad)  
    6d60:	ff                   	(bad)  
    6d61:	ff                   	(bad)  
    6d62:	ff                   	(bad)  
    6d63:	ff                   	(bad)  
    6d64:	ff                   	(bad)  
    6d65:	ff                   	(bad)  
    6d66:	ff                   	(bad)  
    6d67:	ff                   	(bad)  
    6d68:	ff                   	(bad)  
    6d69:	ff                   	(bad)  
    6d6a:	ff                   	(bad)  
    6d6b:	ff                   	(bad)  
    6d6c:	ff                   	(bad)  
    6d6d:	ff                   	(bad)  
    6d6e:	ff                   	(bad)  
    6d6f:	ff                   	(bad)  
    6d70:	ff                   	(bad)  
    6d71:	ff                   	(bad)  
    6d72:	ff                   	(bad)  
    6d73:	ff                   	(bad)  
    6d74:	ff                   	(bad)  
    6d75:	ff                   	(bad)  
    6d76:	ff                   	(bad)  
    6d77:	ff                   	(bad)  
    6d78:	ff                   	(bad)  
    6d79:	ff                   	(bad)  
    6d7a:	ff                   	(bad)  
    6d7b:	ff                   	(bad)  
    6d7c:	ff                   	(bad)  
    6d7d:	ff                   	(bad)  
    6d7e:	ff                   	(bad)  
    6d7f:	ff                   	(bad)  
    6d80:	ff                   	(bad)  
    6d81:	ff                   	(bad)  
    6d82:	ff                   	(bad)  
    6d83:	ff                   	(bad)  
    6d84:	ff                   	(bad)  
    6d85:	ff                   	(bad)  
    6d86:	ff                   	(bad)  
    6d87:	ff                   	(bad)  
    6d88:	ff                   	(bad)  
    6d89:	ff                   	(bad)  
    6d8a:	ff                   	(bad)  
    6d8b:	ff                   	(bad)  
    6d8c:	ff                   	(bad)  
    6d8d:	ff                   	(bad)  
    6d8e:	ff                   	(bad)  
    6d8f:	ff                   	(bad)  
    6d90:	ff                   	(bad)  
    6d91:	ff                   	(bad)  
    6d92:	ff                   	(bad)  
    6d93:	ff                   	(bad)  
    6d94:	ff                   	(bad)  
    6d95:	ff                   	(bad)  
    6d96:	ff                   	(bad)  
    6d97:	ff                   	(bad)  
    6d98:	ff                   	(bad)  
    6d99:	ff                   	(bad)  
    6d9a:	ff                   	(bad)  
    6d9b:	ff                   	(bad)  
    6d9c:	ff                   	(bad)  
    6d9d:	ff                   	(bad)  
    6d9e:	ff                   	(bad)  
    6d9f:	ff                   	(bad)  
    6da0:	ff                   	(bad)  
    6da1:	ff                   	(bad)  
    6da2:	ff                   	(bad)  
    6da3:	ff                   	(bad)  
    6da4:	ff                   	(bad)  
    6da5:	ff                   	(bad)  
    6da6:	ff                   	(bad)  
    6da7:	ff                   	(bad)  
    6da8:	ff                   	(bad)  
    6da9:	ff                   	(bad)  
    6daa:	ff                   	(bad)  
    6dab:	ff                   	(bad)  
    6dac:	ff                   	(bad)  
    6dad:	ff                   	(bad)  
    6dae:	ff                   	(bad)  
    6daf:	ff                   	(bad)  
    6db0:	ff                   	(bad)  
    6db1:	ff                   	(bad)  
    6db2:	ff                   	(bad)  
    6db3:	ff                   	(bad)  
    6db4:	ff                   	(bad)  
    6db5:	ff                   	(bad)  
    6db6:	ff                   	(bad)  
    6db7:	ff                   	(bad)  
    6db8:	ff                   	(bad)  
    6db9:	ff                   	(bad)  
    6dba:	ff                   	(bad)  
    6dbb:	ff                   	(bad)  
    6dbc:	ff                   	(bad)  
    6dbd:	ff                   	(bad)  
    6dbe:	ff                   	(bad)  
    6dbf:	ff                   	(bad)  
    6dc0:	ff                   	(bad)  
    6dc1:	ff                   	(bad)  
    6dc2:	ff                   	(bad)  
    6dc3:	ff                   	(bad)  
    6dc4:	ff                   	(bad)  
    6dc5:	ff                   	(bad)  
    6dc6:	ff                   	(bad)  
    6dc7:	ff                   	(bad)  
    6dc8:	ff                   	(bad)  
    6dc9:	ff                   	(bad)  
    6dca:	ff                   	(bad)  
    6dcb:	ff                   	(bad)  
    6dcc:	ff                   	(bad)  
    6dcd:	ff                   	(bad)  
    6dce:	ff                   	(bad)  
    6dcf:	ff                   	(bad)  
    6dd0:	ff                   	(bad)  
    6dd1:	ff                   	(bad)  
    6dd2:	ff                   	(bad)  
    6dd3:	ff                   	(bad)  
    6dd4:	ff                   	(bad)  
    6dd5:	ff                   	(bad)  
    6dd6:	ff                   	(bad)  
    6dd7:	ff                   	(bad)  
    6dd8:	ff                   	(bad)  
    6dd9:	ff                   	(bad)  
    6dda:	ff                   	(bad)  
    6ddb:	ff                   	(bad)  
    6ddc:	ff                   	(bad)  
    6ddd:	ff                   	(bad)  
    6dde:	ff                   	(bad)  
    6ddf:	ff                   	(bad)  
    6de0:	ff                   	(bad)  
    6de1:	ff                   	(bad)  
    6de2:	ff                   	(bad)  
    6de3:	ff                   	(bad)  
    6de4:	ff                   	(bad)  
    6de5:	ff                   	(bad)  
    6de6:	ff                   	(bad)  
    6de7:	ff                   	(bad)  
    6de8:	ff                   	(bad)  
    6de9:	ff                   	(bad)  
    6dea:	ff                   	(bad)  
    6deb:	ff                   	(bad)  
    6dec:	ff                   	(bad)  
    6ded:	ff                   	(bad)  
    6dee:	ff                   	(bad)  
    6def:	ff                   	(bad)  
    6df0:	ff                   	(bad)  
    6df1:	ff                   	(bad)  
    6df2:	ff                   	(bad)  
    6df3:	ff                   	(bad)  
    6df4:	ff                   	(bad)  
    6df5:	ff                   	(bad)  
    6df6:	ff                   	(bad)  
    6df7:	ff                   	(bad)  
    6df8:	ff                   	(bad)  
    6df9:	ff                   	(bad)  
    6dfa:	ff                   	(bad)  
    6dfb:	ff                   	(bad)  
    6dfc:	ff                   	(bad)  
    6dfd:	ff                   	(bad)  
    6dfe:	ff                   	(bad)  
    6dff:	ff                   	(bad)  
    6e00:	ff                   	(bad)  
    6e01:	ff                   	(bad)  
    6e02:	ff                   	(bad)  
    6e03:	ff                   	(bad)  
    6e04:	ff                   	(bad)  
    6e05:	ff                   	(bad)  
    6e06:	ff                   	(bad)  
    6e07:	ff                   	(bad)  
    6e08:	ff                   	(bad)  
    6e09:	ff                   	(bad)  
    6e0a:	ff                   	(bad)  
    6e0b:	ff                   	(bad)  
    6e0c:	ff                   	(bad)  
    6e0d:	ff                   	(bad)  
    6e0e:	ff                   	(bad)  
    6e0f:	ff                   	(bad)  
    6e10:	ff                   	(bad)  
    6e11:	ff                   	(bad)  
    6e12:	ff                   	(bad)  
    6e13:	ff                   	(bad)  
    6e14:	ff                   	(bad)  
    6e15:	ff                   	(bad)  
    6e16:	ff                   	(bad)  
    6e17:	ff                   	(bad)  
    6e18:	ff                   	(bad)  
    6e19:	ff                   	(bad)  
    6e1a:	ff                   	(bad)  
    6e1b:	ff                   	(bad)  
    6e1c:	ff                   	(bad)  
    6e1d:	ff                   	(bad)  
    6e1e:	ff                   	(bad)  
    6e1f:	ff                   	(bad)  
    6e20:	ff                   	(bad)  
    6e21:	ff                   	(bad)  
    6e22:	ff                   	(bad)  
    6e23:	ff                   	(bad)  
    6e24:	ff                   	(bad)  
    6e25:	ff                   	(bad)  
    6e26:	ff                   	(bad)  
    6e27:	ff                   	(bad)  
    6e28:	ff                   	(bad)  
    6e29:	ff                   	(bad)  
    6e2a:	ff                   	(bad)  
    6e2b:	ff                   	(bad)  
    6e2c:	ff                   	(bad)  
    6e2d:	ff                   	(bad)  
    6e2e:	ff                   	(bad)  
    6e2f:	ff                   	(bad)  
    6e30:	ff                   	(bad)  
    6e31:	ff                   	(bad)  
    6e32:	ff                   	(bad)  
    6e33:	ff                   	(bad)  
    6e34:	ff                   	(bad)  
    6e35:	ff                   	(bad)  
    6e36:	ff                   	(bad)  
    6e37:	ff                   	(bad)  
    6e38:	ff                   	(bad)  
    6e39:	ff                   	(bad)  
    6e3a:	ff                   	(bad)  
    6e3b:	ff                   	(bad)  
    6e3c:	ff                   	(bad)  
    6e3d:	ff                   	(bad)  
    6e3e:	ff                   	(bad)  
    6e3f:	ff                   	(bad)  
    6e40:	ff                   	(bad)  
    6e41:	ff                   	(bad)  
    6e42:	ff                   	(bad)  
    6e43:	ff                   	(bad)  
    6e44:	ff                   	(bad)  
    6e45:	ff                   	(bad)  
    6e46:	ff                   	(bad)  
    6e47:	ff                   	(bad)  
    6e48:	ff                   	(bad)  
    6e49:	ff                   	(bad)  
    6e4a:	ff                   	(bad)  
    6e4b:	ff                   	(bad)  
    6e4c:	ff                   	(bad)  
    6e4d:	ff                   	(bad)  
    6e4e:	ff                   	(bad)  
    6e4f:	ff                   	(bad)  
    6e50:	ff                   	(bad)  
    6e51:	ff                   	(bad)  
    6e52:	ff                   	(bad)  
    6e53:	ff                   	(bad)  
    6e54:	ff                   	(bad)  
    6e55:	ff                   	(bad)  
    6e56:	ff                   	(bad)  
    6e57:	ff                   	(bad)  
    6e58:	ff                   	(bad)  
    6e59:	ff                   	(bad)  
    6e5a:	ff                   	(bad)  
    6e5b:	ff                   	(bad)  
    6e5c:	ff                   	(bad)  
    6e5d:	ff                   	(bad)  
    6e5e:	ff                   	(bad)  
    6e5f:	ff                   	(bad)  
    6e60:	ff                   	(bad)  
    6e61:	ff                   	(bad)  
    6e62:	ff                   	(bad)  
    6e63:	ff                   	(bad)  
    6e64:	ff                   	(bad)  
    6e65:	ff                   	(bad)  
    6e66:	ff                   	(bad)  
    6e67:	ff                   	(bad)  
    6e68:	ff                   	(bad)  
    6e69:	ff                   	(bad)  
    6e6a:	ff                   	(bad)  
    6e6b:	ff                   	(bad)  
    6e6c:	ff                   	(bad)  
    6e6d:	ff                   	(bad)  
    6e6e:	ff                   	(bad)  
    6e6f:	ff                   	(bad)  
    6e70:	ff                   	(bad)  
    6e71:	ff                   	(bad)  
    6e72:	ff                   	(bad)  
    6e73:	ff                   	(bad)  
    6e74:	ff                   	(bad)  
    6e75:	ff                   	(bad)  
    6e76:	ff                   	(bad)  
    6e77:	ff                   	(bad)  
    6e78:	ff                   	(bad)  
    6e79:	ff                   	(bad)  
    6e7a:	ff                   	(bad)  
    6e7b:	ff                   	(bad)  
    6e7c:	ff                   	(bad)  
    6e7d:	ff                   	(bad)  
    6e7e:	ff                   	(bad)  
    6e7f:	ff                   	(bad)  
    6e80:	ff                   	(bad)  
    6e81:	ff                   	(bad)  
    6e82:	ff                   	(bad)  
    6e83:	ff                   	(bad)  
    6e84:	ff                   	(bad)  
    6e85:	ff                   	(bad)  
    6e86:	ff                   	(bad)  
    6e87:	ff                   	(bad)  
    6e88:	ff                   	(bad)  
    6e89:	ff                   	(bad)  
    6e8a:	ff                   	(bad)  
    6e8b:	ff                   	(bad)  
    6e8c:	ff                   	(bad)  
    6e8d:	ff                   	(bad)  
    6e8e:	ff                   	(bad)  
    6e8f:	ff                   	(bad)  
    6e90:	ff                   	(bad)  
    6e91:	ff                   	(bad)  
    6e92:	ff                   	(bad)  
    6e93:	ff                   	(bad)  
    6e94:	ff                   	(bad)  
    6e95:	ff                   	(bad)  
    6e96:	ff                   	(bad)  
    6e97:	ff                   	(bad)  
    6e98:	ff                   	(bad)  
    6e99:	ff                   	(bad)  
    6e9a:	ff                   	(bad)  
    6e9b:	ff                   	(bad)  
    6e9c:	ff                   	(bad)  
    6e9d:	ff                   	(bad)  
    6e9e:	ff                   	(bad)  
    6e9f:	ff                   	(bad)  
    6ea0:	ff                   	(bad)  
    6ea1:	ff                   	(bad)  
    6ea2:	ff                   	(bad)  
    6ea3:	ff                   	(bad)  
    6ea4:	ff                   	(bad)  
    6ea5:	ff                   	(bad)  
    6ea6:	ff                   	(bad)  
    6ea7:	ff                   	(bad)  
    6ea8:	ff                   	(bad)  
    6ea9:	ff                   	(bad)  
    6eaa:	ff                   	(bad)  
    6eab:	ff                   	(bad)  
    6eac:	ff                   	(bad)  
    6ead:	ff                   	(bad)  
    6eae:	ff                   	(bad)  
    6eaf:	ff                   	(bad)  
    6eb0:	ff                   	(bad)  
    6eb1:	ff                   	(bad)  
    6eb2:	ff                   	(bad)  
    6eb3:	ff                   	(bad)  
    6eb4:	ff                   	(bad)  
    6eb5:	ff                   	(bad)  
    6eb6:	ff                   	(bad)  
    6eb7:	ff                   	(bad)  
    6eb8:	ff                   	(bad)  
    6eb9:	ff                   	(bad)  
    6eba:	ff                   	(bad)  
    6ebb:	ff                   	(bad)  
    6ebc:	ff                   	(bad)  
    6ebd:	ff                   	(bad)  
    6ebe:	ff                   	(bad)  
    6ebf:	ff                   	(bad)  
    6ec0:	ff                   	(bad)  
    6ec1:	ff                   	(bad)  
    6ec2:	ff                   	(bad)  
    6ec3:	ff                   	(bad)  
    6ec4:	ff                   	(bad)  
    6ec5:	ff                   	(bad)  
    6ec6:	ff                   	(bad)  
    6ec7:	ff                   	(bad)  
    6ec8:	ff                   	(bad)  
    6ec9:	ff                   	(bad)  
    6eca:	ff                   	(bad)  
    6ecb:	ff                   	(bad)  
    6ecc:	ff                   	(bad)  
    6ecd:	ff                   	(bad)  
    6ece:	ff                   	(bad)  
    6ecf:	ff                   	(bad)  
    6ed0:	ff                   	(bad)  
    6ed1:	ff                   	(bad)  
    6ed2:	ff                   	(bad)  
    6ed3:	ff                   	(bad)  
    6ed4:	ff                   	(bad)  
    6ed5:	ff                   	(bad)  
    6ed6:	ff                   	(bad)  
    6ed7:	ff                   	(bad)  
    6ed8:	ff                   	(bad)  
    6ed9:	ff                   	(bad)  
    6eda:	ff                   	(bad)  
    6edb:	ff                   	(bad)  
    6edc:	ff                   	(bad)  
    6edd:	ff                   	(bad)  
    6ede:	ff                   	(bad)  
    6edf:	ff                   	(bad)  
    6ee0:	ff                   	(bad)  
    6ee1:	ff                   	(bad)  
    6ee2:	ff                   	(bad)  
    6ee3:	ff                   	(bad)  
    6ee4:	ff                   	(bad)  
    6ee5:	ff                   	(bad)  
    6ee6:	ff                   	(bad)  
    6ee7:	ff                   	(bad)  
    6ee8:	ff                   	(bad)  
    6ee9:	ff                   	(bad)  
    6eea:	ff                   	(bad)  
    6eeb:	ff                   	(bad)  
    6eec:	ff                   	(bad)  
    6eed:	ff                   	(bad)  
    6eee:	ff                   	(bad)  
    6eef:	ff                   	(bad)  
    6ef0:	ff                   	(bad)  
    6ef1:	ff                   	(bad)  
    6ef2:	ff                   	(bad)  
    6ef3:	ff                   	(bad)  
    6ef4:	ff                   	(bad)  
    6ef5:	ff                   	(bad)  
    6ef6:	ff                   	(bad)  
    6ef7:	ff                   	(bad)  
    6ef8:	ff                   	(bad)  
    6ef9:	ff                   	(bad)  
    6efa:	ff                   	(bad)  
    6efb:	ff                   	(bad)  
    6efc:	ff                   	(bad)  
    6efd:	ff                   	(bad)  
    6efe:	ff                   	(bad)  
    6eff:	ff                   	(bad)  
    6f00:	ff                   	(bad)  
    6f01:	ff                   	(bad)  
    6f02:	ff                   	(bad)  
    6f03:	ff                   	(bad)  
    6f04:	ff                   	(bad)  
    6f05:	ff                   	(bad)  
    6f06:	ff                   	(bad)  
    6f07:	ff                   	(bad)  
    6f08:	ff                   	(bad)  
    6f09:	ff                   	(bad)  
    6f0a:	ff                   	(bad)  
    6f0b:	ff                   	(bad)  
    6f0c:	ff                   	(bad)  
    6f0d:	ff                   	(bad)  
    6f0e:	ff                   	(bad)  
    6f0f:	ff                   	(bad)  
    6f10:	ff                   	(bad)  
    6f11:	ff                   	(bad)  
    6f12:	ff                   	(bad)  
    6f13:	ff                   	(bad)  
    6f14:	ff                   	(bad)  
    6f15:	ff                   	(bad)  
    6f16:	ff                   	(bad)  
    6f17:	ff                   	(bad)  
    6f18:	ff                   	(bad)  
    6f19:	ff                   	(bad)  
    6f1a:	ff                   	(bad)  
    6f1b:	ff                   	(bad)  
    6f1c:	ff                   	(bad)  
    6f1d:	ff                   	(bad)  
    6f1e:	ff                   	(bad)  
    6f1f:	ff                   	(bad)  
    6f20:	ff                   	(bad)  
    6f21:	ff                   	(bad)  
    6f22:	ff                   	(bad)  
    6f23:	ff                   	(bad)  
    6f24:	ff                   	(bad)  
    6f25:	ff                   	(bad)  
    6f26:	ff                   	(bad)  
    6f27:	ff                   	(bad)  
    6f28:	ff                   	(bad)  
    6f29:	ff                   	(bad)  
    6f2a:	ff                   	(bad)  
    6f2b:	ff                   	(bad)  
    6f2c:	ff                   	(bad)  
    6f2d:	ff                   	(bad)  
    6f2e:	ff                   	(bad)  
    6f2f:	ff                   	(bad)  
    6f30:	ff                   	(bad)  
    6f31:	ff                   	(bad)  
    6f32:	ff                   	(bad)  
    6f33:	ff                   	(bad)  
    6f34:	ff                   	(bad)  
    6f35:	ff                   	(bad)  
    6f36:	ff                   	(bad)  
    6f37:	ff                   	(bad)  
    6f38:	ff                   	(bad)  
    6f39:	ff                   	(bad)  
    6f3a:	ff                   	(bad)  
    6f3b:	ff                   	(bad)  
    6f3c:	ff                   	(bad)  
    6f3d:	ff                   	(bad)  
    6f3e:	ff                   	(bad)  
    6f3f:	ff                   	(bad)  
    6f40:	ff                   	(bad)  
    6f41:	ff                   	(bad)  
    6f42:	ff                   	(bad)  
    6f43:	ff                   	(bad)  
    6f44:	ff                   	(bad)  
    6f45:	ff                   	(bad)  
    6f46:	ff                   	(bad)  
    6f47:	ff                   	(bad)  
    6f48:	ff                   	(bad)  
    6f49:	ff                   	(bad)  
    6f4a:	ff                   	(bad)  
    6f4b:	ff                   	(bad)  
    6f4c:	ff                   	(bad)  
    6f4d:	ff                   	(bad)  
    6f4e:	ff                   	(bad)  
    6f4f:	ff                   	(bad)  
    6f50:	ff                   	(bad)  
    6f51:	ff                   	(bad)  
    6f52:	ff                   	(bad)  
    6f53:	ff                   	(bad)  
    6f54:	ff                   	(bad)  
    6f55:	ff                   	(bad)  
    6f56:	ff                   	(bad)  
    6f57:	ff                   	(bad)  
    6f58:	ff                   	(bad)  
    6f59:	ff                   	(bad)  
    6f5a:	ff                   	(bad)  
    6f5b:	ff                   	(bad)  
    6f5c:	ff                   	(bad)  
    6f5d:	ff                   	(bad)  
    6f5e:	ff                   	(bad)  
    6f5f:	ff                   	(bad)  
    6f60:	ff                   	(bad)  
    6f61:	ff                   	(bad)  
    6f62:	ff                   	(bad)  
    6f63:	ff                   	(bad)  
    6f64:	ff                   	(bad)  
    6f65:	ff                   	(bad)  
    6f66:	ff                   	(bad)  
    6f67:	ff                   	(bad)  
    6f68:	ff                   	(bad)  
    6f69:	ff                   	(bad)  
    6f6a:	ff                   	(bad)  
    6f6b:	ff                   	(bad)  
    6f6c:	ff                   	(bad)  
    6f6d:	ff                   	(bad)  
    6f6e:	ff                   	(bad)  
    6f6f:	ff                   	(bad)  
    6f70:	ff                   	(bad)  
    6f71:	ff                   	(bad)  
    6f72:	ff                   	(bad)  
    6f73:	ff                   	(bad)  
    6f74:	ff                   	(bad)  
    6f75:	ff                   	(bad)  
    6f76:	ff                   	(bad)  
    6f77:	ff                   	(bad)  
    6f78:	ff                   	(bad)  
    6f79:	ff                   	(bad)  
    6f7a:	ff                   	(bad)  
    6f7b:	ff                   	(bad)  
    6f7c:	ff                   	(bad)  
    6f7d:	ff                   	(bad)  
    6f7e:	ff                   	(bad)  
    6f7f:	ff                   	(bad)  
    6f80:	ff                   	(bad)  
    6f81:	ff                   	(bad)  
    6f82:	ff                   	(bad)  
    6f83:	ff                   	(bad)  
    6f84:	ff                   	(bad)  
    6f85:	ff                   	(bad)  
    6f86:	ff                   	(bad)  
    6f87:	ff                   	(bad)  
    6f88:	ff                   	(bad)  
    6f89:	ff                   	(bad)  
    6f8a:	ff                   	(bad)  
    6f8b:	ff                   	(bad)  
    6f8c:	ff                   	(bad)  
    6f8d:	ff                   	(bad)  
    6f8e:	ff                   	(bad)  
    6f8f:	ff                   	(bad)  
    6f90:	ff                   	(bad)  
    6f91:	ff                   	(bad)  
    6f92:	ff                   	(bad)  
    6f93:	ff                   	(bad)  
    6f94:	ff                   	(bad)  
    6f95:	ff                   	(bad)  
    6f96:	ff                   	(bad)  
    6f97:	ff                   	(bad)  
    6f98:	ff                   	(bad)  
    6f99:	ff                   	(bad)  
    6f9a:	ff                   	(bad)  
    6f9b:	ff                   	(bad)  
    6f9c:	ff                   	(bad)  
    6f9d:	ff                   	(bad)  
    6f9e:	ff                   	(bad)  
    6f9f:	ff                   	(bad)  
    6fa0:	ff                   	(bad)  
    6fa1:	ff                   	(bad)  
    6fa2:	ff                   	(bad)  
    6fa3:	ff                   	(bad)  
    6fa4:	ff                   	(bad)  
    6fa5:	ff                   	(bad)  
    6fa6:	ff                   	(bad)  
    6fa7:	ff                   	(bad)  
    6fa8:	ff                   	(bad)  
    6fa9:	ff                   	(bad)  
    6faa:	ff                   	(bad)  
    6fab:	ff                   	(bad)  
    6fac:	ff                   	(bad)  
    6fad:	ff                   	(bad)  
    6fae:	ff                   	(bad)  
    6faf:	ff                   	(bad)  
    6fb0:	ff                   	(bad)  
    6fb1:	ff                   	(bad)  
    6fb2:	ff                   	(bad)  
    6fb3:	ff                   	(bad)  
    6fb4:	ff                   	(bad)  
    6fb5:	ff                   	(bad)  
    6fb6:	ff                   	(bad)  
    6fb7:	ff                   	(bad)  
    6fb8:	ff                   	(bad)  
    6fb9:	ff                   	(bad)  
    6fba:	ff                   	(bad)  
    6fbb:	ff                   	(bad)  
    6fbc:	ff                   	(bad)  
    6fbd:	ff                   	(bad)  
    6fbe:	ff                   	(bad)  
    6fbf:	ff                   	(bad)  
    6fc0:	ff                   	(bad)  
    6fc1:	ff                   	(bad)  
    6fc2:	ff                   	(bad)  
    6fc3:	ff                   	(bad)  
    6fc4:	ff                   	(bad)  
    6fc5:	ff                   	(bad)  
    6fc6:	ff                   	(bad)  
    6fc7:	ff                   	(bad)  
    6fc8:	ff                   	(bad)  
    6fc9:	ff                   	(bad)  
    6fca:	ff                   	(bad)  
    6fcb:	ff                   	(bad)  
    6fcc:	ff                   	(bad)  
    6fcd:	ff                   	(bad)  
    6fce:	ff                   	(bad)  
    6fcf:	ff                   	(bad)  
    6fd0:	ff                   	(bad)  
    6fd1:	ff                   	(bad)  
    6fd2:	ff                   	(bad)  
    6fd3:	ff                   	(bad)  
    6fd4:	ff                   	(bad)  
    6fd5:	ff                   	(bad)  
    6fd6:	ff                   	(bad)  
    6fd7:	ff                   	(bad)  
    6fd8:	ff                   	(bad)  
    6fd9:	ff                   	(bad)  
    6fda:	ff                   	(bad)  
    6fdb:	ff                   	(bad)  
    6fdc:	ff                   	(bad)  
    6fdd:	ff                   	(bad)  
    6fde:	ff                   	(bad)  
    6fdf:	ff                   	(bad)  
    6fe0:	ff                   	(bad)  
    6fe1:	ff                   	(bad)  
    6fe2:	ff                   	(bad)  
    6fe3:	ff                   	(bad)  
    6fe4:	ff                   	(bad)  
    6fe5:	ff                   	(bad)  
    6fe6:	ff                   	(bad)  
    6fe7:	ff                   	(bad)  
    6fe8:	ff                   	(bad)  
    6fe9:	ff                   	(bad)  
    6fea:	ff                   	(bad)  
    6feb:	ff                   	(bad)  
    6fec:	ff                   	(bad)  
    6fed:	ff                   	(bad)  
    6fee:	ff                   	(bad)  
    6fef:	ff                   	(bad)  
    6ff0:	ff                   	(bad)  
    6ff1:	ff                   	(bad)  
    6ff2:	ff                   	(bad)  
    6ff3:	ff                   	(bad)  
    6ff4:	ff                   	(bad)  
    6ff5:	ff                   	(bad)  
    6ff6:	ff                   	(bad)  
    6ff7:	ff                   	(bad)  
    6ff8:	ff                   	(bad)  
    6ff9:	ff                   	(bad)  
    6ffa:	ff                   	(bad)  
    6ffb:	ff                   	(bad)  
    6ffc:	ff                   	(bad)  
    6ffd:	ff                   	(bad)  
    6ffe:	ff                   	.byte 0xff
    6fff:	5d                   	pop    %bp
