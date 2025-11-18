import { useState } from 'react'
import { TextField } from "@radix-ui/themes";
import { SearchIcon } from "lucide-react";
import Card from './components/card'

function App() {

  return (
    <>
        <div className="flex flex-col items-center justify-center h-screen">
          <h1 className="text-7xl font-bold">FitsIt</h1>
          
          <div className="w-full max-w-sm my-10">
            <TextField.Root size="3" placeholder="Search for item" >
              <TextField.Slot>
                <SearchIcon height="20" width="20" />
              </TextField.Slot>
            </TextField.Root>
          </div>

        <div className="flex flex-wrap gap-4">
          <Card />
          <Card />  
          <Card />
          <Card />
        </div>

        </div> 
    </>
  )
}

export default App
