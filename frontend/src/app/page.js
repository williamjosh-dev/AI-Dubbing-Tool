'use client';
import { useState } from 'react';

export default function DubbingStudio() {
  // Form State
  const [file, setFile] = useState(null);
  const [srcLang, setSrcLang] = useState('es');
  const [tgtLang, setTgtLang] = useState('en');
  const [voiceClone, setVoiceClone] = useState(false);
  const [voiceMethod, setVoiceMethod] = useState('auto');
  const [outputFormat, setOutputFormat] = useState('wav');
  const [enhanceAudio, setEnhanceAudio] = useState(false);

  // App UI State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    // Prepare exactly what app.py expects via Form data
    const formData = new FormData();
    formData.append('audioFile', file);
    formData.append('srcLang', srcLang);
    formData.append('tgtLang', tgtLang);
    formData.append('voiceClone', voiceClone ? 'on' : 'off');
    formData.append('voiceMethod', voiceMethod);
    formData.append('outputFormat', outputFormat);
    formData.append('enhanceAudio', enhanceAudio ? 'on' : 'off');

    try {
      const response = await fetch('http://127.0.0.1:5000/api/dub', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to process media file.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Something went wrong connecting to FastAPI.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] font-sans antialiased p-6 md:p-12">
      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Input Form Control Dashboard */}
        <div className="lg:col-span-5 bg-[#161b22] border border-[#30363d] rounded-xl p-6 shadow-xl h-fit">
          <header className="mb-6 border-b border-[#30363d] pb-4">
            <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
              🎙️ AI Dubbing Studio
            </h1>
            <p className="text-sm text-[#8b949e] mt-1">Translate audio & video files seamlessly</p>
          </header>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* File Upload Zone */}
            <div>
              <label className="block text-sm font-medium mb-2 text-[#e6edf3]">Upload Media File</label>
              <div className="relative border-2 border-dashed border-[#30363d] hover:border-[#58a6ff] rounded-lg p-4 transition-colors bg-[#0d1117] text-center cursor-pointer">
                <input 
                  type="file" 
                  onChange={handleFileChange} 
                  required 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <span className="text-sm text-[#8b949e]">
                  {file ? `📁 ${file.name}` : 'Click or Drag files here (MP4, MP3, WAV...)'}
                </span>
              </div>
            </div>

            {/* Language Configuration Dropdowns */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1.5 text-[#e6edf3]">Source Language</label>
                <input 
                  type="text" 
                  value={srcLang} 
                  onChange={(e) => setSrcLang(e.target.value)} 
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-white focus:outline-none focus:border-[#58a6ff] text-sm"
                  placeholder="e.g. es"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5 text-[#e6edf3]">Target Language</label>
                <input 
                  type="text" 
                  value={tgtLang} 
                  onChange={(e) => setTgtLang(e.target.value)} 
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-white focus:outline-none focus:border-[#58a6ff] text-sm"
                  placeholder="e.g. en"
                />
              </div>
            </div>

            {/* Technical Pipeline Settings */}
            <div className="border-t border-[#30363d] pt-4 space-y-4">
              <h3 className="text-sm font-semibold text-white">Pipeline Parameters</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5 text-[#e6edf3]">Voice Method</label>
                  <select 
                    value={voiceMethod} 
                    onChange={(e) => setVoiceMethod(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-white focus:outline-none text-sm"
                  >
                    <option value="auto">Auto Select</option>
                    <option value="male">Male Vector</option>
                    <option value="female">Female Vector</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5 text-[#e6edf3]">Output Format</label>
                  <select 
                    value={outputFormat} 
                    onChange={(e) => setOutputFormat(e.target.value)}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-white focus:outline-none text-sm"
                  >
                    <option value="wav">WAV Lossless</option>
                    <option value="mp3">MP3 Compressed</option>
                  </select>
                </div>
              </div>

              {/* Toggles for Pipeline Add-ons */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer text-sm text-[#e6edf3]">
                  <input 
                    type="checkbox" 
                    checked={voiceClone} 
                    onChange={(e) => setVoiceClone(e.target.checked)}
                    className="accent-[#238636] h-4 w-4"
                  />
                  Enable Voice Cloning (AI Engine)
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-sm text-[#e6edf3]">
                  <input 
                    type="checkbox" 
                    checked={enhanceAudio} 
                    onChange={(e) => setEnhanceAudio(e.target.checked)}
                    className="accent-[#238636] h-4 w-4"
                  />
                  Run FFmpeg Audio Enhancement
                </label>
              </div>
            </div>

            {/* Execute Processing Submission Trigger */}
            <button 
              type="submit" 
              disabled={loading} 
              className={`w-full font-semibold rounded-md py-2.5 text-sm transition-colors text-white ${
                loading ? 'bg-[#216e39] cursor-not-allowed text-[#8b949e]' : 'bg-[#238636] hover:bg-[#2ea043]'
              }`}
            >
              {loading ? '⚡ Running Generation Pipeline...' : 'Generate AI Dubbing'}
            </button>
          </form>
        </div>

        {/* Right Column: Output Interactive Render Screen */}
        <div className="lg:col-span-7 bg-[#161b22] border border-[#30363d] rounded-xl p-6 shadow-xl flex flex-col min-h-[450px]">
          <h2 className="text-xl font-bold border-b border-[#30363d] pb-4 mb-4 text-white">
            🖥️ Media Output Dashboard
          </h2>

          {/* Fallback Idle / Loading Screens */}
          {!loading && !result && !error && (
            <div className="flex-1 flex flex-col items-center justify-center text-[#8b949e] border border-dashed border-[#30363d] rounded-lg bg-[#0d1117]">
              <span className="text-4xl mb-2">🎬</span>
              <p className="text-sm">Configure settings and click generate to process media files.</p>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-[#58a6ff] border border-dashed border-[#30363d] rounded-lg bg-[#0d1117] animate-pulse">
              <span className="text-4xl mb-2">⚙️</span>
              <p className="text-sm font-medium">Processing transcripts, translating nodes, and synthesizing text-to-speech...</p>
            </div>
          )}

          {error && (
            <div className="flex-1 flex flex-col items-center justify-center text-[#ff7b72] border border-[#f85149]/30 rounded-lg bg-[#f85149]/10 p-4 text-center">
              <span className="text-3xl mb-2">⚠️ Pipeline Failure</span>
              <p className="text-sm max-w-md">{error}</p>
            </div>
          )}

          {/* Render Result Dashboard Outputs */}
          {result && (
            <div className="space-y-6 flex-1">
              <div className="bg-[#0d1117] p-4 rounded-lg border border-[#30363d]">
                <h4 className="text-xs uppercase tracking-wider text-[#8b949e] font-semibold mb-3">Generated Output Track</h4>
                {result.videoUrl ? (
                  <video src={`http://127.0.0.1:5000${result.videoUrl}`} controls className="w-full rounded border border-[#30363d]" />
                ) : (
                  <audio src={`http://127.0.0.1:5000${result.audioUrl}`} controls className="w-full mt-1" />
                )}
              </div>

              <div className="flex items-center gap-3 mt-3">
                {result.videoUrl && (
                  <a href={`http://127.0.0.1:5000${result.videoUrl}`} target="_blank" rel="noreferrer" className="px-4 py-2 bg-[#238636] rounded text-white text-sm">Open Video</a>
                )}
                {result.audioUrl && (
                  <a href={`http://127.0.0.1:5000${result.audioUrl}`} download className="px-4 py-2 bg-[#238636] rounded text-white text-sm">Download Audio</a>
                )}

                <button onClick={() => { setResult(null); setFile(null); }} className="ml-auto text-sm text-[#8b949e] hover:text-white">New Job</button>
              </div>

              {result.transcript && (
                <div className="mt-4 bg-[#0d1117] p-4 rounded border border-[#30363d] text-sm text-[#8b949e] max-h-36 overflow-auto">
                  <h5 className="font-semibold text-white mb-2">Transcript</h5>
                  <pre className="whitespace-pre-wrap">{result.transcript}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
