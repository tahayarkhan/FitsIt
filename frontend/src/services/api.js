import axios from "axios";


const API_URL = import.meta.env.VITE_BACKEND;

export const searchPinterest = async (item) => {

    if (!item) return null;
    
    const modifiedQuery = `${item} pinterest fit inspirations`

    const { data } = await axios.get(`${API_URL}/pinterest`, {
        params: { query: modifiedQuery, num: 2 }
    });    
    
    console.log(data);
    return data;
};

