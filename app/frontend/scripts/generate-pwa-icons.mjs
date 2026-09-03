import { deflateSync } from "node:zlib";
import { writeFileSync } from "node:fs";
import { join } from "node:path";

const crcTable = new Uint32Array(256).map((_, index) => {
  let value = index;
  for (let bit = 0; bit < 8; bit++) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0);
  return value >>> 0;
});

function crc32(buffer) {
  let value = 0xffffffff;
  for (const byte of buffer) value = crcTable[(value ^ byte) & 0xff] ^ (value >>> 8);
  return (value ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBuffer = Buffer.from(type, "ascii");
  const result = Buffer.alloc(12 + data.length);
  result.writeUInt32BE(data.length, 0);
  typeBuffer.copy(result, 4);
  data.copy(result, 8);
  result.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])), 8 + data.length);
  return result;
}

function writeIcon(size) {
  const pixels = Buffer.alloc(size * size * 4);
  const triangleTop = Math.round(size * 0.234);
  const triangleBottom = Math.round(size * 0.488);
  const circleCenter = Math.round(size * 0.645);
  const circleRadius = Math.round(size * 0.078);
  const radius = Math.round(size * 0.195);

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const index = (y * size + x) * 4;
      const dx = Math.max(Math.abs(x - size / 2) - (size / 2 - radius), 0);
      const dy = Math.max(Math.abs(y - size / 2) - (size / 2 - radius), 0);
      const insideRoundedSquare = dx * dx + dy * dy <= radius * radius;
      const triangleHalfWidth = Math.round((y - triangleTop) * 0.72);
      const inTriangle = y >= triangleTop && y <= triangleBottom && Math.abs(x - size / 2) <= triangleHalfWidth;
      const inCircle = (x - size / 2) ** 2 + (y - circleCenter) ** 2 <= circleRadius ** 2;
      const color = inTriangle || inCircle ? [255, 255, 255, 255] : insideRoundedSquare ? [14, 165, 233, 255] : [0, 0, 0, 0];
      pixels.set(color, index);
    }
  }

  const scanlines = Buffer.alloc((size * 4 + 1) * size);
  for (let y = 0; y < size; y++) {
    const offset = y * (size * 4 + 1);
    scanlines[offset] = 0;
    pixels.copy(scanlines, offset + 1, y * size * 4, (y + 1) * size * 4);
  }

  const header = Buffer.alloc(13);
  header.writeUInt32BE(size, 0);
  header.writeUInt32BE(size, 4);
  header[8] = 8;
  header[9] = 6;
  const png = Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk("IHDR", header),
    chunk("IDAT", deflateSync(scanlines)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
  writeFileSync(join(process.cwd(), "public", `icon-${size}x${size}.png`), png);
}

writeIcon(192);
writeIcon(512);
