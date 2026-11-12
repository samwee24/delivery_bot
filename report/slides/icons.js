const React = require('react'); const { renderToStaticMarkup } = require('react-dom/server'); const sharp = require('sharp');
const tb = require('react-icons/tb');
const names = ['TbGauge', 'TbChartDots', 'TbBroadcast', 'TbRefreshOff', 'TbSteeringWheel', 'TbArrowBarToDown', 'TbVolumeOff',
  'TbHourglass', 'TbClockExclamation', 'TbPlugConnectedX', 'TbPower'];
(async () => {
  for (const n of names) for (const [tag, col] of [['ink', '#111111'], ['white', '#FFFFFF']]) {
    const svg = renderToStaticMarkup(React.createElement(tb[n], { color: col, size: 256 }));
    await sharp(Buffer.from(svg)).png().toFile(`icons/${n}_${tag}.png`);
  }
  console.log('done', names.length);
})();
