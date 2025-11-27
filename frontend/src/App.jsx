import { useState } from 'react'
import { TextField } from "@radix-ui/themes";
import { SearchIcon } from "lucide-react";
import CardComponent from './components/card'
import { searchPinterest } from './services/api';

function App() {

  const [item, setItem] = useState("");
  const [images, setImages] = useState([]);

  const handleSubmit = async(e) => {
    e.preventDefault();
    const data = await searchPinterest(item);
    setImages(data.images);
  }

  return (
    <>
        <div className="flex flex-col items-center justify-center w-full mt-10">
          <h1 className="text-7xl font-bold">FitsIt</h1>
          
          <div className="w-full max-w-sm my-10">
            <form onSubmit={handleSubmit}>
              <TextField.Root size="3" placeholder="Search for item" value={item} onChange={(e) => setItem(e.target.value)}>
                <TextField.Slot>
                  <SearchIcon height="20" width="20" />
                </TextField.Slot>
              </TextField.Root>
            </form>


          </div>

        <div className="flex flex-wrap gap-4 justify-center items-center">
          
          {images.map((src, i) => (
            <CardComponent key={i} src={src} />
          ))}
     
        </div>

        </div> 
    </>
  )
}

export default App
