'use client';
import { useState, useEffect, FormEvent } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface Document {
  id: string;
  title: string;
  total_chunks: number;
  upload_date: string;
}

interface Source {
  doc_id: string;
  doc_title: string;
  chunk_id: number;
  score: number;
  text_preview?: string;
}

interface Message {
  question: string;
  answer: string;
  method: string;
  score?: number;
  sources?: Source[];
}

export default function Dashboard() {
  const { user, logout, loading } = useAuth();
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<Document[]>([]);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push('/');
  }, [user, loading]);

  useEffect(() => {
    if (user) fetchDocuments();
  }, [user]);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents');
      setDocuments(res.data.documents);
    } catch (err) {
      console.error('Failed to fetch documents');
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    let successCount = 0;
    let failCount = 0;

    for (const file of Array.from(files)) {
      const formData = new FormData();
      formData.append('file', file);

      try {
        await api.post('/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        successCount++;
      } catch (err: any) {
        failCount++;
      }
    }

    if (failCount === 0) {
      toast.success(`${successCount} document(s) uploaded successfully`);
    } else {
      toast.success(`${successCount} uploaded, ${failCount} failed`);
    }
    
    fetchDocuments();
    setUploading(false);
    e.target.value = '';
  };

  const toggleDocument = (doc: Document) => {
    setSelectedDocs((prev) => {
      const isSelected = prev.find((d) => d.id === doc.id);
      if (isSelected) {
        return prev.filter((d) => d.id !== doc.id);
      } else {
        return [...prev, doc];
      }
    });
    setMessages([]);
  };

  const handleAsk = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim() || selectedDocs.length === 0) return;

    setLoadingMsg(true);
    const currentQuestion = question;
    setQuestion('');

    try {
      const res = await api.post('/query', {
        question: currentQuestion,
        document_ids: selectedDocs.map((d) => d.id),
        chat_history: messages.slice(-6),
        top_k: 3,
        search_method: 'embedding',
      });

      setMessages((prev) => [
        ...prev,
        {
          question: currentQuestion,
          answer: res.data.answer,
          method: res.data.search_method,
          score: res.data.best_score,
          sources: res.data.retrieved_chunks || [],
        },
      ]);
    } catch (err: any) {
      toast.error('Failed to get answer');
    } finally {
      setLoadingMsg(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#0A0A0B]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-[#E8E3D5] border-t-transparent rounded-full animate-spin" />
          <p className="text-[#6B6760] text-sm">Loading workspace...</p>
        </div>
      </div>
    );
  }

  const selectedCount = selectedDocs.length;

  return (
    <div className="h-screen flex overflow-hidden" style={{ background: '#0A0A0B', fontFamily: "'DM Sans', sans-serif" }}>
      {/* Sidebar */}
      <aside
        className="flex flex-col border-r transition-all duration-300 overflow-hidden"
        style={{
          width: sidebarOpen ? '280px' : '0px',
          minWidth: sidebarOpen ? '280px' : '0px',
          background: '#0F0F10',
          borderColor: '#1C1C1E',
        }}
      >
        <div className="flex items-center gap-3 px-5 py-5 border-b" style={{ borderColor: '#1C1C1E' }}>
          <div className="w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold" style={{ background: '#E8E3D5', color: '#0A0A0B' }}>AI</div>
          <span className="text-sm font-semibold tracking-tight" style={{ color: '#E8E3D5' }}>DocMind</span>
        </div>

        <div className="px-4 py-4">
          <input type="file" accept=".pdf" multiple onChange={handleUpload} disabled={uploading} className="hidden" id="pdf-upload" />
          <button
            type="button"
            onClick={() => {
              const input = document.getElementById('pdf-upload') as HTMLInputElement;
              if (input) input.click();
            }}
            disabled={uploading}
            className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg cursor-pointer text-sm font-medium transition-all duration-150"
            style={{ background: uploading ? '#1C1C1E' : '#E8E3D5', color: uploading ? '#6B6760' : '#0A0A0B' }}
          >
            {uploading ? (
              <>
                <div className="w-3.5 h-3.5 border border-[#6B6760] border-t-transparent rounded-full animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                Upload PDFs
              </>
            )}
          </button>
          <p className="text-[10px] text-center mt-2" style={{ color: '#3D3D40' }}>You can select multiple files</p>
        </div>

        {selectedCount > 0 && (
          <div className="px-4 pb-2">
            <div className="flex items-center justify-between px-3 py-2 rounded-lg text-xs" style={{ background: '#1C1C1E', color: '#E8E3D5', border: '1px solid #2E2E30' }}>
              <span>{selectedCount} selected</span>
              <button onClick={() => { setSelectedDocs([]); setMessages([]); }} className="text-[#E8625A] hover:underline">Clear</button>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <p className="text-[10px] font-semibold tracking-widest uppercase mb-3" style={{ color: '#3D3D40' }}>Documents</p>
          <div className="space-y-1">
            {documents.map((doc) => {
              const isSelected = !!selectedDocs.find((d) => d.id === doc.id);
              return (
                <button
                  key={doc.id}
                  onClick={() => toggleDocument(doc)}
                  className="w-full text-left px-3 py-2.5 rounded-lg transition-all duration-150 flex items-start gap-2.5"
                  style={{ background: isSelected ? '#1C1C1E' : 'transparent', border: `1px solid ${isSelected ? '#E8E3D5' : 'transparent'}` }}
                >
                  <div className="w-4 h-4 rounded flex items-center justify-center shrink-0 mt-0.5" style={{ background: isSelected ? '#E8E3D5' : 'transparent', border: `1.5px solid ${isSelected ? '#E8E3D5' : '#3D3D40'}` }}>
                    {isSelected && <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#0A0A0B" strokeWidth="3"><polyline points="20 6 9 17 4 12" /></svg>}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium truncate" style={{ color: isSelected ? '#E8E3D5' : '#8A8A8E' }}>{doc.title}</p>
                    <p className="text-[10px] mt-0.5" style={{ color: '#3D3D40' }}>{doc.total_chunks} chunks</p>
                  </div>
                </button>
              );
            })}
            {documents.length === 0 && (
              <div className="py-8 text-center">
                <p className="text-xs" style={{ color: '#3D3D40' }}>No documents yet</p>
              </div>
            )}
          </div>
        </div>

        <div className="px-4 py-4 border-t flex items-center justify-between" style={{ borderColor: '#1C1C1E' }}>
          <span className="text-xs truncate" style={{ color: '#6B6760' }}>{user?.name}</span>
          <button onClick={handleLogout} className="text-[11px]" style={{ color: '#E8625A' }}>Logout</button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center gap-3 px-5 py-3.5 border-b shrink-0" style={{ background: '#0A0A0B', borderColor: '#1C1C1E' }}>
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1.5 rounded-md" style={{ color: '#4A4A4E' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></svg>
          </button>
          {selectedCount > 0 ? (
            <div>
              <span className="text-sm font-medium" style={{ color: '#E8E3D5' }}>{selectedCount} document{selectedCount > 1 ? 's' : ''} selected</span>
              {messages.length > 0 && (
                <span className="text-[10px] ml-2 px-2 py-0.5 rounded-full" style={{ background: '#1C1C1E', color: '#4A4A4E', border: '1px solid #2E2E30' }}>
                  🧠 Memory active
                </span>
              )}
            </div>
          ) : (
            <span className="text-sm" style={{ color: '#3D3D40' }}>Select documents to begin</span>
          )}
        </header>

        <div className="flex-1 overflow-y-auto">
          {messages.length > 0 && (
            <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
              {messages.map((msg, i) => (
                <div key={i} className="space-y-4">
                  <div className="flex justify-end">
                    <div className="max-w-xl px-4 py-3 rounded-2xl rounded-br-sm text-sm" style={{ background: '#1C1C1E', color: '#E8E3D5' }}>{msg.question}</div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold shrink-0" style={{ background: '#E8E3D5', color: '#0A0A0B' }}>AI</div>
                    <div className="flex-1 min-w-0">
                      <div className="px-4 py-3 rounded-2xl rounded-tl-sm text-sm" style={{ background: '#0F0F10', color: '#C8C4B8', border: '1px solid #1C1C1E' }}>{msg.answer}</div>
                      
                      {/* 🆕 Sources Citation */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-2 px-1">
                          <div className="flex items-center gap-1 mb-1">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#4A4A4E" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                            <span className="text-[10px] font-medium" style={{ color: '#4A4A4E' }}>Sources</span>
                          </div>
                          <div className="space-y-0.5">
                            {msg.sources.slice(0, 3).map((src, j) => (
                              <div key={j} className="flex items-center gap-2 text-[10px] pl-3 py-0.5 rounded" style={{ color: '#6B6760' }}>
                                <span style={{ color: '#E8E3D5' }}>📑</span>
                                <span className="truncate font-medium" style={{ color: '#8A8A8E' }}>{src.doc_title}</span>
                                <span style={{ color: '#3D3D40' }}>·</span>
                                <span style={{ color: '#3D3D40' }}>Chunk {src.chunk_id}</span>
                                <span className="ml-auto text-[10px]" style={{ color: '#4A4A4E' }}>{(src.score * 100).toFixed(0)}%</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {loadingMsg && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] font-bold" style={{ background: '#E8E3D5', color: '#0A0A0B' }}>AI</div>
                  <div className="px-4 py-3.5 rounded-2xl rounded-tl-sm" style={{ background: '#0F0F10', border: '1px solid #1C1C1E' }}>
                    <div className="flex gap-1.5">
                      {[0, 150, 300].map((d) => <div key={d} className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#3D3D40', animationDelay: `${d}ms` }} />)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {selectedCount > 0 && (
          <div className="shrink-0 px-6 py-5 border-t" style={{ background: '#0A0A0B', borderColor: '#1C1C1E' }}>
            <form onSubmit={handleAsk} className="max-w-3xl mx-auto">
              <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl" style={{ background: '#0F0F10', border: '1px solid #2E2E30' }}>
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={messages.length > 0 ? "Ask a follow-up question..." : `Search across ${selectedCount} document${selectedCount > 1 ? 's' : ''}...`}
                  disabled={loadingMsg}
                  className="flex-1 bg-transparent text-sm outline-none"
                  style={{ color: '#E8E3D5' }}
                />
                <button type="submit" disabled={loadingMsg || !question.trim()} className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: question.trim() && !loadingMsg ? '#E8E3D5' : '#1C1C1E', color: question.trim() && !loadingMsg ? '#0A0A0B' : '#3D3D40' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}